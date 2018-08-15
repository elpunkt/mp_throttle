import multiprocessing
import queue
import time, os
from itertools import dropwhile


class Throttle:
    """Central object to store the multiprocessing shared objects and create the throttling and the monitoring process.

    :param max_n:
        Number of allowed processes per time unit 'per'
    :type max_n: ``int``
    :param per:
        Time in seconds that max_n if reffering to.
    :type per: ``int``
    :param \**kwargs:
        See below

    :Keyword Arguments:
        * *as_monitor* (``bool``) --
          If True (default): Monitoring process will be created.
        * *as_throttle* (``bool``) --
          If True (default): Monitoring process will be created.
        * *auto_emit* (``bool``) --
          If True (default): A timestamp will be passed to the monitoring process, each time :meth:`await_fuel` or :meth:`has_fuel` is called.
          If False: :meth:`emit` can be called by the processes to submit a timestamp to the monitoring process.
        * *auto_calibrate* (``bool``) --
          If True (default for max_n >= 49): and as_throttle = True and _correction not set manually: :meth:`_calibrate` gets called when instatiating.
          If False (default for max_n <= 49): :meth:`_calibrate` will not get called.
        * *_correction* (``float``) --
          Factor to reduce the frequency with which the gas queue is filled. If set manually, :meth:`_calibrate` will not get called.
        * *hardcap* (``str``) --
          If 'limit' (default): The gas queue will never exceed max_n (Optimising latest frequency).
          If 'one': The gas queue will never exceed 1 (Preventig to ever exceed max_n processes per second)
          Else: The gas queue might exceed max_n when worker processes are slower (Optimising mean frequency).
        * *rf_rate* (``float``) --
          Time in second between each update of the monitoring process. Can not be 0. Defaul 0.01.


    """
    def __init__(self, max_n = 0, per = 1, **kwargs):
        self.max_n = max_n
        self.per = per
        self.as_monitor = kwargs.get('as_monitor', True)
        self.as_throttle = kwargs.get('as_throttle', True)
        self.auto_emit = kwargs.get('auto_emit', True if self.as_throttle == True else False)
        self.auto_calibrate = kwargs.get('auto_calibrate', True if self.max_n/self.per >= 49 else False)
        self.hardcap = kwargs.get('hardcap', 'limit')
        self.refresh_rate = kwargs.get('rf_rate', 0.01)
        if self.refresh_rate == 0:
            raise Exception("rf_rate can not be 0.")
        self._correction = kwargs.get('_correction', 0)
        if self.auto_calibrate and self.as_throttle and self._correction == 0:
            self._calibrate()

        self.kill_flag = multiprocessing.Event()
        self.emissions = multiprocessing.Queue()
        self.gas = multiprocessing.Queue()

        self.monitor_process = None
        self.throttle_process = None

        # Statistics
        self.highest_s_per_p = multiprocessing.Value('d', 0)
        self.lowest_s_per_p = multiprocessing.Value('d', 9999999)
        self.latest_p_per_s = multiprocessing.Value('d', 0)
        self.latest_s_per_p = multiprocessing.Value('d', 0)
        self.mean_p_per_s = multiprocessing.Value('d', 0)
        self.mean_s_per_p = multiprocessing.Value('d', 0)
        self.total_n = multiprocessing.Value('i', 0)

        self.start_time = multiprocessing.Value('d', 0)
        self.runtime = multiprocessing.Value('d', 0)


    def _start_throttle(self):
        if self.hardcap == 'limit':
            _fill_tank_hc(self.gas, self.kill_flag,self.max_n,self.per/self.max_n, self._correction)
        elif self.hardcap == 'one':
            _fill_tank_hc_one(self.gas, self.kill_flag, self.per/self.max_n, self._correction)
        else:
            _fill_tank(self.gas, self.kill_flag, self.per/self.max_n, self._correction)

    def _start_monitor(self):
        _calculate_freq(self.emissions,
                        self.kill_flag,
                        self.total_n,
                        self.latest_p_per_s,
                        self.latest_s_per_p,
                        self.mean_p_per_s,
                        self.mean_s_per_p,
                        self.lowest_s_per_p,
                        self.highest_s_per_p,
                        self.start_time,
                        self.runtime,
                        self.refresh_rate)
        return

    def start(self):
        ''' Starts the monitoring and throttle process and sets self.start_time.'''
        self.start_time.value = time.time()
        if self.as_monitor:
            self.monitor_process = multiprocessing.Process(target=self._start_monitor, daemon=True)
            self.monitor_process.start()
        if self.as_throttle:
            self.throttle_process = multiprocessing.Process(target=self._start_throttle, daemon=True)
            self.throttle_process.start()

    def stop(self):
        ''' Stops the throttle and the monitoring process, empties the gas and the emission queue and resets the lates stats.
            Returns (runtime, total emissions, mean time between emissions, mean emissions per second)'''
        self.kill_flag.set()
        if self.throttle_process != None:
            self.throttle_process.join()
        if self.monitor_process != None:
            self.monitor_process.join()
        stop_time = time.time()
        self.runtime.value += stop_time - self.start_time.value
        self.latest_p_per_s.value = 0
        self.latest_s_per_p.value = 0
        while self.gas.empty == False:
            self.gas.get()
        while self.emissions.empty == False:
            self.emissions.get()
        self.kill_flag.clear()
        return (self.runtime.value, self.total_n.value, self.mean_s_per_p.value, self.mean_p_per_s.value)

    def has_fuel(self):
        ''' Returns True if fuel is available, else False. For blocking unitl fuel is available use :meth:`await_fuel` '''
        try:
            self.gas.get_nowait()
            if self.auto_emit:
                self.emissions.put(time.time())
            return True
        except queue.Empty:
            return False

    def await_fuel(self, t=None):
        ''' Blocks the calling process until fuel is available (return True) or timeout seconds have passed (return False).

            :param t:
                timeout in seconds. Default = None (unlimited timeout).
            :type t: ``float``

        '''
        try:
            self.gas.get(timeout=t)
            if self.auto_emit:
                self.emissions.put(time.time())
            return True
        except queue.Empty:
            return False

    def emit(self, timestamp = None):
        ''' Passes a timestamp to the monitoring process. Can be called anywhere in each worker process, if self.auto_emit = False.

            :param timestamp:
                Optional: Submit a specific timestamp to the monitoring process. If not specified, time.time() will be submitted.
            :type timestamp: ``float (epoch-time)``

        '''
        if self.auto_emit:
            raise Exception('auto_emit == True. Set it to False to emit manually.')
        else:
            if type(timestamp) != float:
                timestamp = time.time()
            self.emissions.put(timestamp)

    def latest(self):
        ''' Returns the stats of the last second as tuple (time between emissions, emissions per second) '''
        if not self.as_monitor:
            raise Exception("Monitor not running. Set 'as_monitor=True'")
        s_per_p = 1/self.latest_p_per_s.value if self.latest_p_per_s.value > 0 else 0
        return (s_per_p, self.latest_p_per_s.value)

    def mean(self):
        ''' Returns the mean stats as tuple (mean time between emissions, mean emissions per second) '''
        if not self.as_monitor:
            raise Exception("Monitor not running. Set 'as_monitor=True'")
        return (1/self.mean_p_per_s.value if self.mean_p_per_s.value > 0 else 0 , self.mean_p_per_s.value)

    def lo_hi(self):
        ''' Returns the lowest time between emission and the highest emissions per second.'''
        if not self.as_monitor:
            raise Exception("Monitor not running. Set 'as_monitor=True'")
        return (self.lowest_s_per_p.value, 1/self.lowest_s_per_p.value )

    def hi_lo(self):
        ''' Returns the highest time between emission and the lowest emissions per second.'''
        if not self.as_monitor:
            raise Exception("Monitor not running. Set 'as_monitor=True'")
        return (self.highest_s_per_p.value, 1/self.highest_s_per_p.value if self.highest_s_per_p.value > 0 else 0  )



    def _calibrate(self):
        ''' Calculates a correction thats is used to adapt the frequency in which fuel is put into the tank.
            If Throttle.auto_calibrate == True, this function is called when creating a Throttle object.'''
        tmp_throttle = Throttle(self.max_n, self.per, auto_calibrate=False)
        ps = os.cpu_count()
        dummyworker = multiprocessing.Pool(processes=ps, initializer=_dummywork, initargs=(tmp_throttle,))
        tmp_throttle.start()
        time.sleep(1)
        self._correction = 1 - tmp_throttle.stop()[1]/(self.max_n/self.per)#+(self.max_n/self.per)/1000000


def _fill_tank(tank, kill_flag, frequency, correction):
    while not kill_flag.is_set():
        tank.put(1)
        time.sleep(frequency-frequency*correction)

def _fill_tank_hc(tank, kill_flag, max_n, frequency, correction):
    while not kill_flag.is_set():
        if not tank.qsize() >= max_n:
            tank.put(None)
        time.sleep(frequency-frequency*correction)

def _fill_tank_hc_one(tank, kill_flag, frequency, correction):
    while not kill_flag.is_set():
        if tank.empty():
            tank.put(1)
        time.sleep(frequency-frequency*correction)


def _calculate_freq(emissions, kill_flag, total_n, latest_p_per_s, latest_s_per_p, mean_p_per_s, mean_s_per_p, lowest_s_per_p, highest_s_per_p, start_time, runtime, refresh_rate):
    temp = []
    while not kill_flag.is_set():
        while not emissions.empty():
            temp.append(emissions.get_nowait())
            total_n.value += 1
        temp = list(dropwhile(lambda x: x < time.time() - 1, temp))
        latest_p_per_s.value = len(temp)
        for i, p in enumerate(temp):
            try:
                s_per_p = temp[i+1] - p
                if s_per_p < lowest_s_per_p.value:
                    lowest_s_per_p.value = s_per_p
                if s_per_p > highest_s_per_p.value:
                    highest_s_per_p.value = s_per_p
            except IndexError:
                pass
        mean_p_per_s.value = total_n.value / (time.time() - start_time.value + runtime.value)
        time.sleep(refresh_rate)
    return

def _dummywork(throttle):
    while True:
        throttle.await_fuel()
