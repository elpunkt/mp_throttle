========
Tutorial
========

This module allows to throttle and monitor processes from Pythons multiprocessing package. 

Terminology
-----------
To illustrate the communication between throttle, monitor and worker processes this module uses a specific terminology. Each worker process needs "fuel" to run. The throttle limits the number of processes by only providing limited "fuel". By using "fuel" each process creates "emissions". These are counted by the monitor.

Throttle you processes
----------------------
To get started simply import and instantiate the central :class:`mp_throttle.Throttle` class. As a first argument it takes the maximum number of processes that should run in a specified time. As a the second argumnet you can specify the time (tyically one second).::

  import multiprocessing
  import mp_throttle
  import time
  throttle = mp_throttle.Throttle(4,1)

So throttle = Throttle(4,1) can be read as "Create a throttle to limit the processes to 4 per 1 second." To test it, create some worker processes and pass the throttle instance to them.::

  def work(tank):
      while not tank.kill_flag.is_set():
          # Block until 'fuel' is available.
          tank.await_fuel()
          # do something and repeat.
  workerpool = multiprocessing.Pool(processes=4, initializer=work, initargs=(throttle,))

The Throttle.kill_flag is a multiprocessing.Event and can be used to stop the worker processes together with the throttle. :meth:`mp_throttle.Throttle.await_fuel` blocks the worker processes until there is 'fuel' in the tank. To test it run :meth:`mp_throttle.Throttle.start`, wait for as long as you wish, then run :meth:`mp_throttle.Throttle.stop` to set the kill_flag and stop all processes. It furthermore returns the final state in form of a tuple (runtime, total_emissions, mean_time_between_processes, mean_processes_per_second)::

  throttle.start()
  time.sleep(5)
  runtime, total_emissions, mean_time_between_processes, mean_processes_per_second = throttle.stop()
  print("Runtime: {}".format(runtime))
  print("Total: {}".format(total_emissions))
  print("Time between processes: {}".format(mean_time_between_processes))
  print("Processes per second: {}".format(mean_processes_per_second))

This should print out something like::

  >>> Runtime: 5.0189573764801025
  >>> Total: 25
  >>> Time between processes: 0.2002760696411133
  >>> Processes per second: 4.993107772645828

Get the stats
-------------
If you need to access the stats during runtime you can call :meth:`mp_throttle.Throttle.latest` to receive the stats for the last second or :meth:`mp_throttle.Throttle.mean` to receive the average stats::

  throttle.start()
  for i in range(10):
      print(throttle.latest())
      print(throttle.mean())
      time.sleep(0.5)
  
  runtime, total_processes, mean_time_between_processes, mean_processes_per_second = throttle.stop()
  print("Runtime: {}".format(runtime))
  print("Total: {}".format(total_processes))
  print("Time between processes: {}".format(mean_time_between_processes))
  print("Processes per second: {}".format(mean_processes_per_second))


This should add something like the following to the output::

  >>> ...
  >>> (0.2, 5)
  >>> (0.20075019730461968, 4.981315153990077)
  >>> (0.2, 5)
  >>> (0.19862029949824014, 5.034732112106499)
  >>> Runtime: 10.054526805877686
  >>> Total: 50
  >>> Time between processes: 0.20071841716766356
  >>> Processes per second: 4.982103855296361







