.. currentmodule:: mp_throttle

*****
Guide
*****

By default mp_throttle starts a throttling and a monitoring process when calling :meth:`Throttle.start`. However if you only need specific functions you can set ``as_throttle=False`` or ``as_monitor=False`` when instantiating.

Throttle Mode
*************
Activated by default. Deactivate by setting ``as_throttle=False``. The throttle is a ``multiprocessing.Process`` that puts fuel in the gas queue according to your settings.


.. _accuracy:

Accuracy and calibration
========================

Precisely throttling processes on a per second base is hard to accomplish. While the Throttle works fairly well out of the box in the range of up to 10 processes per second, you will find it less accurate in higher ranges. This is due to many constraints:

* `Unsteady fuel consumption`: The throttle puts fuel into the gas queue at the defined rate. However your processes propably do not consume the fuel steadily. Image you want to throttle your worker processes to 4/1 second. When all worker proceeses are busy the gas queue fills up to 4. When they now finish their task around the same time, they all start immidiately again. At last 1/4 of a second later, with the next iteration of the throttle process, the tank fills again and the fuel might be consumed by a worker process immidiately. This would lead to 5 processes started within roughly over 0.25 seconds. **Solution**: use the `hardcap` property.

* `System sleep time`. The time.sleep(t) accuracy and the minimum time.sleep(t) t depends on your system (`Read more <https://stackoverflow.com/questions/1133857/how-accurate-is-pythons-time-sleep/>`_)  **Solution**: Set a `_correction` factor for the sleep time. The :meth:`Throttle._calibrate` method is used if `auto_calibrate=True` or if `max_n/per >= 49`and no custom `calibration` is provided.

Options
=======
* ``hardcap (str)``: Defines the throttling behaviour. If set to 'limit' (default), the gas queue will never exceed max_n (Optimising latest frequency). If set to 'one', the gas queue will never exceed 1 to prevent ever exceeding ``max_n`` processes per second. Otherwise, the gas queue might exceed max_n when worker processes are slower. That way the processes per second might exceed ``max_n`` per second, but the average over runtime will be optimised.
* ``auto_emit (bool)``: If true (default) eacht time a worker process consumes fuel, this is immidiately reported to the monitor process. If you wish to report at a later point (e.g. after a worker process has finished successfully) set ``auto_emit=False`` and use :meth:`Throttle.emit`
* ``auto_calibrate``: If True (default for max_n >= 49), :meth:`Throttle._calibrate` will be called when instantiating and calculate a ``_correction`` for the throttle process. If you instantiate with a ``_correction`` set, the :meth:`Throttle._calibrate` will not run.
* ``_correction (float)``: Correction for the throttle process sleep time. After putting fuel in the queue, the throttle process sleeps for ``per/max_n-per/max_n*_correction`` seconds.

Methods:
========
* :meth:`Throttle.has_fuel` tries to get fuel immidiately and returns False if the gas queue is empty, else True.
* :meth:`Throttle.await_fuel` blocks the calling process until fuel is available (return True) or timeout seconds ``t (optional)`` have passed (return False).



Monitor Mode
************
Activated by default. Deactivate by setting ``as_monitor=False``. The monitor is a ``multiprocessing.Process`` that counts the "emissions" of your processes.

Options
=======
The only option to set is ``rf_rate``. It sets the time in seconds that the monitoring process sleeps between calculating the current stats.

Methods:
========

* :meth:`Throttle.emit` counts +1. Use whenever a worker process has done something countworthy. If you do not specify a timestamp in form the epoch-time
* :meth:`Throttle.mean`, :meth:`Throttle.latest`, :meth:`Throttle.lo_hi` and :meth:`Throttle.hi_lo` return statistics in form of a tuple ``(time_between_emission, emissions_per_second)``
* :meth:`Throttle.stop` stops/pauses the monitor and returns ``(runtime, total_emissions, mean_time_between_emissions, mean_emissions_per_second)`` the runtime and the statistics are preserved so that they will continued when starting the monitor again.


Alternatively you could access the specific values directly via your :class:`Throttle` instance.
