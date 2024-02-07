# All rights reserved. Cyan Changes (c) 2024
# Licensed to lovemilk-Inc@proton.me under Apache-2.0

import asyncio
import atexit
import datetime
import inspect
import threading

from contextvars import copy_context, Context
from functools import partial, wraps
from threading import Thread
from asyncio import run, Future, Task, Queue as AsyncQueue
from queue import Queue, Empty as EmptyException
from dataclasses import dataclass, field
from typing import Callable, ParamSpec, TypeVar, Coroutine, Awaitable, cast, Any, Sequence, Optional
from itertools import count

__all__ = [
    'set_timeout',
    'set_interval',
    'clear_timeout',
    'clear_interval',
    'SchedulerThread',
    'WorkerThread',
    'shutdown'
]

MAX_TASK_NUM = 0
WORKERS_NUM = 2

P = ParamSpec("P")
R = TypeVar("R")


def run_sync(call: Callable[P, R]) -> Callable[P, Coroutine[None, None, R]]:
    """一个用于包装 sync function 为 async function 的装饰器

    参数:
        call: 被装饰的同步函数
    """

    @wraps(call)
    async def _wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        loop = asyncio.get_running_loop()
        p_func = partial(call, *args, **kwargs)
        context = copy_context()
        result = await loop.run_in_executor(None, partial(context.run, p_func))
        return result

    return _wrapper


def is_coroutine_callable(call: Callable[..., Any]) -> bool:
    """检查 call 是否是一个 callable 协程函数"""
    if inspect.isroutine(call):
        return inspect.iscoroutinefunction(call)
    if inspect.isclass(call):
        return False
    func_ = getattr(call, "__call__", None)
    return inspect.iscoroutinefunction(func_)


def _transform_handler(func: Callable[[], Awaitable]):
    if is_coroutine_callable(func):
        return cast(Callable[..., Awaitable], func)
    else:
        return run_sync(cast(Callable[..., Any], func))


@dataclass
class ScheduledTask:
    func: Callable
    call_at: datetime.datetime
    _interval: bool = None
    id: int = None
    context: Optional[Context] = None
    args: Sequence = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)

    @property
    def is_interval(self):
        return bool(self._interval)


@dataclass(frozen=True)
class Timer:
    __id: int
    __task: ScheduledTask = field(repr=False)

    def __hash__(self):
        return hash(self.__id)


def _id_of(timer: Timer) -> int:
    return getattr(timer, f'__{type(Timer).__name__}_id')


class SchedulerThread(Thread):
    def __init__(self, workers_cnt=WORKERS_NUM):
        super().__init__()
        self.fut = Future()
        self._tasks: dict[int, Task] = {}
        self._counter = count(0)
        self.stop_event = threading.Event()
        self.workers: list[WorkerThread] = [WorkerThread(self, self.stop_event) for _ in range(workers_cnt)]
        self.cancelled_ids: AsyncQueue[int] = AsyncQueue()
        self.pending_tasks: AsyncQueue["ScheduledTask"] = AsyncQueue(maxsize=MAX_TASK_NUM)
        self.waiting_tasks: Queue["ScheduledTask"] = Queue(maxsize=MAX_TASK_NUM)
        self._loop = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        return self._loop

    def start(self):
        super().start()

        for worker in self.workers:
            worker.start()

    def add_task(self, task: ScheduledTask):
        task.id = next(self._counter)
        self.waiting_tasks.put(task)

    async def _schedule_task(self, at: datetime.datetime, task: ScheduledTask):
        assert task.id is not None
        while not self.fut.done():
            await asyncio.sleep((datetime.datetime.now() - at).total_seconds())
            await self.pending_tasks.put(task)
            if not task._interval:
                break

    def _task(self, i: int, coro: Coroutine, loop: asyncio.AbstractEventLoop):
        _t = loop.create_task(coro, name=f'ScheduledTask-{i}')
        self._tasks[i] = _t
        return _t

    async def canceller(self):
        while not self.fut.done():
            _id = await self.cancelled_ids.get()
            task = self._tasks.get(_id, None)
            if task is not None:
                task.cancel()

    async def main(self):
        loop = asyncio.get_running_loop()
        self._loop = loop
        while not self.fut.done():
            try:
                task = self.waiting_tasks.get_nowait()
            except EmptyException:
                continue
            finally:
                await asyncio.sleep(0)

            _ = self._task(task.id, self._schedule_task(task.call_at, task), loop)

    def stop(self):
        self.stop_event.set()
        self.fut.set_result(None)
        self._get_loop().stop()

    def join(self, timeout=None):
        super().join(timeout)
        for worker in self.workers:
            worker.join()

    def run(self):
        run(self.main())


def call_task(task: ScheduledTask):
    if task.context is not None:
        task.context.run(task.func, *task.args, **task.kwargs)
    else:
        task.func(*task.args, **task.kwargs)


class WorkerThread(Thread):
    def __init__(self, scheduler: SchedulerThread, stop_event: threading.Event):
        super().__init__()
        self.scheduler = scheduler
        self.stop_event = stop_event

    async def main(self):
        loop = asyncio.get_running_loop()

        while not self.scheduler.fut.done():
            if self.stop_event.is_set():
                break

            fut = asyncio.run_coroutine_threadsafe(self.scheduler.pending_tasks.get(), self.scheduler._get_loop())
            task = fut.result()

            await loop.run_in_executor(
                None, partial(call_task, task)
            )

    async def wait_and_main(self):
        while self.scheduler._get_loop() is None:
            await asyncio.sleep(0.01)

        if self.scheduler.fut.done():
            return

        assert not self.stop_event.is_set()
        await self.main()

    def run(self):
        try:
            run(self.wait_and_main())
        finally:
            pass


_scheduler = SchedulerThread()
_scheduler.start()


def set_timeout(func: Callable, timeout: float, __scheduler: SchedulerThread = _scheduler, *args, **kwargs) -> Timer:
    sc = __scheduler
    task = ScheduledTask(
        func=func,
        args=args, kwargs=kwargs,
        call_at=datetime.datetime.now() + datetime.timedelta(seconds=timeout)
    )
    sc.add_task(task)
    return Timer(task.id, task)


def clear_timeout(timer: Timer, __scheduler: SchedulerThread = _scheduler) -> None:
    sc = __scheduler
    _id = _id_of(timer)
    sc.cancelled_ids.put_nowait(_id)


def set_interval(func: Callable, timeout: float, __scheduler: SchedulerThread = _scheduler, *args, **kwargs) -> Timer:
    sc = __scheduler
    task = ScheduledTask(
        func=func,
        args=args, kwargs=kwargs,
        call_at=datetime.datetime.now() + datetime.timedelta(seconds=timeout),
        _interval=True
    )
    sc.add_task(task)
    return Timer(task.id, task)


def shutdown(__scheduler: SchedulerThread = _scheduler) -> None:
    sc = __scheduler
    sc.stop()
    sc.join()


atexit.register(partial(shutdown))

clear_interval = clear_timeout
