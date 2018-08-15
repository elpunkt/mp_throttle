# mp_throttle
#### A Python package to monitor and throttle multiprocessing processes.

## Use case:
This package can be used to control and monitor Pythons [multiprocessing](https://docs.python.org/3.4/library/multiprocessing.html?highlight=process) processes. The central Throttle class can be used to monitor the current and the mean frequency of processes and/or to throttle your processes to execute a limited times per second. This can be used to limit the server requests of a multi-process web crawler.

## Example:
```python
    import multiprocessing
    import mp_throttle
    import time

    def work(tank):
        while not tank.kill_flag.is_set():
            # Block until 'fuel' is available.
            tank.await_fuel()
            # do something
        return

    # Limit the processes to 4 per 1 second, by providing 4 'fuel' per second.
    throttle = mp_throttle.Throttle(4,1)
    workerpool = multiprocessing.Pool(processes=4, initializer=work, initargs=(throttle,))
    throttle.start()
    time.sleep(5)
    # Stops the processes and return stats:
    runtime, total_processes, mean_frequency, mean_processes_per_second = throttle.stop()
    print("Runtime: {}".format(runtime))
    print("Total: {}".format(total_processes))
    print("Mean frequency: {}".format(mean_frequency))
    print("Processes per second: {}".format(mean_processes_per_second))
```
Output:

    >>> Runtime: 5.027516841888428
    >>> Total: 20
    >>> Mean frequency: 0.25046865940093993
    >>> Processes per second: 3.9925154803469485


## Installation:

To install mp_throttle, simply use pip:

    pip install mp_throttle


## Documentation:
For the full documentation see [docs.elpunkt.eu](http://docs.elpunkt.eu/mp_throttle)

## How to Contribute:
1. Test mp_throttle and open an issue to report a bug or discuss a feature idea.
2. Give general feedback on the code and the package structure. Since this is my first python package, I'm sure there is a lot to feedback on:)
3. Fork the repository and make your changes.
