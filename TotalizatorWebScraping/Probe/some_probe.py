import logging
import threading
import time
import concurrent.futures
import random
import queue

SENTINEL = object()


class FakeDatabase:
    """
    Класс для демонстрации возникновния состояния гонки (race conditions) - гоники за общеие ресурсы
    эмулирует работу с записем и чтением данных в абстрактную базу данных

    особенность в следущем: в многопоточном запуске экземпляра класса FakeDatabase запускается один и тот же метод
    эксземпляра. но локальные переменные принадлежат каждому потоку. переменные экземпляра общие. в методе update
    идет копирование в локальную переменную значение переменной экземпляра. затем значение локальной переменной
    увеличивается на единицу и идет засыпание на долю секунды. В этот момент ОС передает управление в другой поток.
    Другой потока так же копирует в локальную переменную значение переменной экземпляра класса, которое еще не
    обновилось в первом потоке. Таким образом произошло состояние гонки: другой поток взял состояние переменной до
    того момента пока его обнвленное значение не сохранил предыдущий поток.
    """

    def __init__(self):
        self.value = 0

    def update(self, name):
        logging.info("Thread %s: starting update", name)
        local_copy = self.value
        local_copy += 1
        time.sleep(0.1)
        self.value = local_copy
        logging.info("Thread %s: finishing update", name)


class FakeDatabaseSolved:
    def __init__(self):
        self.value = 0
        self._lock = threading.Lock()

    def update(self, name):
        logging.info("Thread %s: starting update", name)
        logging.debug("     Thread %s about to lock", name)
        with self._lock:
            logging.debug("     Thread %s has lock", name)
            local_copy = self.value
            local_copy += 1
            time.sleep(0.1)
            self.value = local_copy
            logging.debug("     Thread %s about release lock", name)
        logging.debug("     Thread %s after release", name)
        logging.info("Thread %s: finishing update", name)


class Pipeline:
    """
    в примере с производителе-потребителе класс  виде ковеера который получает сообщения от производителя и передает
    их потребителю, в одну операцию передается один объект
    """

    def __init__(self):
        self.message = 0
        self.producer_lock = threading.Lock()
        self.consumer_lock = threading.Lock()
        self.consumer_lock.acquire()

    def get_message(self, name):
        logging.debug("     %s: about to acquire getlock", name)
        self.consumer_lock.acquire()
        logging.debug("     %s: have getlock", name)
        message = self.message
        logging.debug("     %s: about to released setlock", name)
        self.producer_lock.release()
        logging.debug("     %s: setlock realesed", name)

        # при включенное ниже сроке произойдет состояние гонки, когда в момент засыпания
        # отработает параллельный поток с Производителем и изменит значение self.message
        # time.sleep(0.1)
        if message != self.message:
            logging.critical("message:%s  !=  self.message:%s", message, self.message)
        return message

    def set_message(self, message, name):
        logging.debug("     %s: about to acquire setlock", name)
        self.producer_lock.acquire()
        logging.debug("     %s: have setlock", name)
        self.message = message
        logging.debug("     %s: about to release getlock", name)
        self.consumer_lock.release()
        logging.debug("     %s: getlock released", name)


class PipelineQueue(queue.Queue):
    """
    в примере с производителе-потребителе класс  виде ковеера который получает сообщения от производителя и передает
    их потребителю, в качестве транспорта используется очередь класса queue.Queue - от которого произошло наследование
    класса
    """

    def __init__(self):
        super().__init__(maxsize=10)
        self.added, self.saved = [], []

    def __del__(self):
        logging.info("Added:%d of %s", len(self.added), self.added)
        logging.info("Saved:%d of %s", len(self.saved), self.saved)

    def get_message(self, name):
        logging.debug("     %s: about to get queue", name)
        value = self.get()
        self.saved.append(value)
        logging.debug("     %s: got %d from queue", name, value)
        return value

    def set_message(self, value, name):
        logging.debug("     %s: about to add %d to queue", name, value)
        self.put(value)
        self.added.append(value)
        logging.debug("     %s: added %d to queue", name, value)


def thread_function(name):
    logging.info("Thread %s: starting", name)
    time.sleep(2)
    logging.info("                        Thread %s: finishing", name)


def set_logging():
    format = "%(asctime)s (%(threadName)-9s): %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%d/%m/%Y %H:%M:%S")
    logging.getLogger().setLevel(logging.INFO)
    # logging.getLogger().setLevel(logging.DEBUG)
    # logging.getLogger().setLevel(logging.WARNING)


def main_1():
    """
    пример с запуском нескольких потоков.
    особенности:
        - в первом цикле создаются и запускайются 3 обычных потока (не демонов) и добавляются в список threads
        - во втором цикле ожидается заверщение выполнения работы потоков через метод join()
    :return:
    """
    threads = list()
    for index in range(3):
        logging.info("Main    : create and start thread %d.", index)
        x = threading.Thread(target=thread_function, args=(index,))
        x.setName(f'Thread {index+1}')
        threads.append(x)
        x.start()

    for index, thread in enumerate(threads):
        logging.info("Main    : before joining thread %d.", index)
        thread.join()
        logging.info("Main    : thread %d done", index)


def main_2():
    """
        Упрощенный вариант запуска потоков через TreadPoolExecutor.
        В его конструктор передается максимальное количество паралельных потоков
        Работа потоков выполняется в контекстном менеджаре with - это настоятельная рекоммендация Python, которая
        гарантирует выполнение метода join() для каждого запущенного потока.
        :return:
        """

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        executor.map(thread_function, range(3))


def main_3():
    """
    фнкция демонстрирует случай с состоянием гонки (race condition) при работе в многопоточнос приложении
    вызов экземпляра класса FakeDatabase - демонстрирует случай с состоянием гонки.
    вызов экземпляра класса FakeDatabaseSolved - демонстрирует как исключить состояние гонки.
    :return:
    """
    # database = FakeDatabase()
    database = FakeDatabaseSolved()
    logging.info("Testing update. Starting value is %d.", database.value)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        for index in range(4):
            executor.submit(database.update, index)
    logging.info("Testing update. Ending value is %d.", database.value)


def producer(pipeline):
    """
    эмулируем получение сообщения из сети
    :param pipeline:
    :return:
    """
    logging.info("Producer start working")
    for index in range(10):
        message = random.randint(1, 101)
        logging.info("Producer got message: %s", message)
        pipeline.set_message(message, "Producer")

    # Send a sentiel message to tell consumer we're done
    pipeline.set_message(SENTINEL, "Producer")


def consumer(pipeline):
    """
    эмулируем получение сообщений от производителя и сохранение их в базу данных
    :param pipeline: PipelineQueue
    :return:
    """
    logging.info("Consumer start working")
    message = 0
    while message is not SENTINEL:
        message = pipeline.get_message("Consumer")
        if message is not SENTINEL:
            logging.info("Consumer storing message: %s", message)


def producer_PipelineQueue(pipeline: PipelineQueue, event: threading.Event):
    """
    эмулируем получение сообщения из сети
    в примере используется очередь
    :param
        pipeline: PipelineQueue()
        evenr: queue.Queue()
    :return:
    """
    logging.info("Producer start working")
    while not event.is_set():
        message = random.randint(1, 101)
        logging.info("Producer got message: %s", message)
        pipeline.set_message(message, "Producer")

    logging.info("Producer received EXIT event, Exiting")


def consumer_PipelineQueue(pipeline: PipelineQueue, event: threading.Event):
    """
    эмулируем получение сообщений от производителя и сохранение их в базу данных
    в примере используется очередь
    :param
        pipeline: PipelineQueue()
        evenr: queue.Queue()
    :return:
    """
    logging.info("Consumer start working")
    while not event.is_set() or not pipeline.empty():
        message = pipeline.get_message("Consumer")
        logging.info(
            "Consumer storing message: %s   (queue size=%s)",
            message,
            pipeline.qsize(),
        )
    logging.info("Consumer received EXIT event. Exiting")


def main_4():
    """
    Пример эмулирует работу производителя-потребителя в многопоточном режиме
    в даннвом примере потоки обмениваются только одним сообщением
    :return:
    """
    logging.critical("Start program")
    pipeline = Pipeline()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(producer, pipeline)
        executor.submit(consumer, pipeline)
    logging.critical("Stop program")


def main_5_producer_consumer_PipelineQueue():
    """
    Пример эмулирует работу производителя-потребителя в многопоточном режиме
    данный пример демонстрирует обмен сообщениями в очереди threading.Queue
    :return:
    """
    logging.critical("Start program")
    pipeline = PipelineQueue()
    event = threading.Event()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(producer_PipelineQueue, pipeline, event)
        executor.submit(consumer_PipelineQueue, pipeline, event)

        time.sleep(0.002)
        logging.info("Main: about to set event")
        event.set()

    logging.critical("Stop program")


def producer_queue(queue: queue.Queue, event: threading.Event):
    """
    Пример эмулирует работу производителя-потребителя в многопоточном режиме
    данный пример демонстрирует обмен сообщениями в очереди threading.Queue
    """
    while not event.is_set():
        message = random.randint(1, 101)
        queue.put(message)
        logging.info("Producer: в очередь добавдено сообшение %s (длина очереди:%d)", message, queue.qsize())
    logging.info("Produser: Получено сообшение о закрытии")


def consumer_queue(queue: queue.Queue, event: threading.Event):

    while not event.is_set() or not queue.empty():
        event_message = 0
        message = queue.get()
        logging.info("      Consumer: получено из очереди сообщение %s (длина очереди:%d)", message, queue.qsize())
        if event.is_set() and event_message==0:
            logging.info("      Consumer: получено сообщение о закрытии")
            event_message += 1


def main_6_producer_consumer_queue():
    pipeline = queue.Queue(maxsize=10)
    event = threading.Event()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(producer_queue, pipeline, event)
        executor.submit(consumer_queue, pipeline, event)

        time.sleep(0.001)
        logging.info("Main: перед вызовом события")
        event.set()


if __name__ == "__main__":
    set_logging()
    main_6_producer_consumer_queue()
    # main_2()
