### Fill in the following information before submitting
# Group id: 42
# Members: Dylan Tanaka, Nathan Loo, Kanec Olivares

from collections import deque

# PID is just an integer, but it is used to make it clear when a integer is expected to be a valid PID.
PID = int

# This class represents the PCB of processes.
# It is only here for your convinience and can be modified however you see fit.
class PCB:
    pid: PID
    priority: int
    def __init__(self, pid: PID, priority: int = -1):
        self.pid = pid
        self.priority = priority

# class Mutex:
#     lock: bool
#     def __init__(self, lock: bool = False):
#         self.lock = lock

# class Semaphore:
#     init_val: int
#     initialized: bool
#     def __init__(self, init_val: int = 0, initialized: bool = False):
#         self.init_val = int
#         self.initialized = initialized
        
# This class represents the Kernel of the simulation.
# The simulator will create an instance of this object and use it to respond to syscalls and interrupts.
# DO NOT modify the name of this class or remove it.
class Kernel:
    scheduling_algorithm: str
    ready_queue: deque[PCB]
    waiting_queue: dict
    running: PCB
    idle_pcb: PCB
    sem_list: list # key: sem_num value: number of semphors left
    mutex_list: list

    # Called before the simulation begins.
    # Use this method to initilize any variables you need throughout the simulation.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def __init__(self, scheduling_algorithm: str, logger):
        self.scheduling_algorithm = scheduling_algorithm
        self.ready_queue = deque()
        self.waiting_queue = {} # key: resources being waited for value: list of pcbs waiting for resource
        self.idle_pcb = PCB(0)
        self.running = self.idle_pcb
        self.logger = logger
        
        self.current_process_run_time = 0  # For keeping track of time for RR

        if self.scheduling_algorithm == "Multilevel":
            self.fg = Kernel("RR", logger)
            self.bg = Kernel("FCFS", logger)
        self.level = "fg"
        self.ml_runtime = 0

        # This is for the semophor and mutex part
        self.sem_list = []
        self.mutex_list = []

    # This method is triggered every time a new process has arrived.
    # new_process is this process's PID.
    # priority is the priority of new_process.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def new_process_arrived(self, new_process: PID, priority: int, process_type: str) -> PID:
        if self.scheduling_algorithm == "Multilevel":
            fg_running, bg_running = self.fg.running.pid, self.bg.running.pid
            if process_type == "Foreground":
                fg_running = self.fg.new_process_arrived(new_process, priority, process_type)
            elif process_type == "Background":
                bg_running = self.bg.new_process_arrived(new_process, priority, process_type)

            if self.level == "fg":
                if fg_running == 0 and (self.bg.running is not self.bg.idle_pcb or len(self.bg.ready_queue)!= 0):
                    self.ml_runtime = 0
                    #self.logger.log("switched to bg")
                    self.level = "bg"
                    return self.bg.running.pid
                else:
                    return fg_running
            elif self.level == "bg":
                if bg_running == 0 and (self.fg.running is not self.fg.idle_pcb or len(self.fg.ready_queue) != 0):
                    self.ml_runtime = 0
                    #self.logger.log("switched to fg")
                    self.level = "fg"
                    return self.fg.running.pid
                else:
                    return bg_running
                
        new_PCB = PCB(new_process, priority)
        self.ready_queue.append(new_PCB)        
        
        if self.scheduling_algorithm == "RR" or self.scheduling_algorithm == "FCFS":
            if self.running is self.idle_pcb:
                self.running = self.choose_next_process()
            return self.running.pid
       
        elif self.scheduling_algorithm == "Priority":
            self.running = self.choose_next_process()
            return self.running.pid

    def p(self, msg):
        if True:
            self.logger.log(msg)

    # This method is triggered every time the current process performs an exit syscall.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_exit(self) -> PID:
        if self.scheduling_algorithm == "Multilevel":
            if self.level == "fg":
                running = self.fg.syscall_exit()
                if running == 0 and (self.bg.running is not self.bg.idle_pcb or len(self.bg.ready_queue)!= 0):
                    self.ml_runtime = 0
                    self.level = "bg"
                    return self.bg.running.pid
                else:
                    return running
            elif self.level == "bg":
                running = self.bg.syscall_exit()
                if running == 0 and (self.fg.running is not self.fg.idle_pcb or len(self.fg.ready_queue) != 0):
                    self.ml_runtime = 0
                    self.level = "fg"
                    return self.fg.running.pid
                else:
                    return running

        if self.scheduling_algorithm == "Priority":
            self.ready_queue.remove(self.running)
            self.running = self.choose_next_process()
            return self.running.pid

        if self.scheduling_algorithm == "RR" or self.scheduling_algorithm == "FCFS":
            self.running = self.choose_next_process()
            return self.running.pid

    # This method is triggered when the currently running process requests to change its priority.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_set_priority(self, new_priority: int) -> PID:
        if self.scheduling_algorithm == "Multilevel":
            if self.level == "fg":
                return self.fg.syscall_set_priority(new_priority)
            elif self.level == "bg":
                return self.bg.syscall_set_priority(new_priority)

        self.running.priority = new_priority
        self.running = self.choose_next_process()
        return self.running.pid


    # This is where you can select the next process to run.
    # This method is not directly called by the simulator and is purely for your convinience.
    # Feel free to modify this method as you see fit.
    # It is not required to actually use this method but it is recommended.
    def choose_next_process(self) -> PCB:
        if len(self.ready_queue) == 0:
            return self.idle_pcb

        if self.scheduling_algorithm == "FCFS":
            return self.ready_queue.popleft()

        elif self.scheduling_algorithm == "Priority":
            smallest_priority = self.ready_queue[0]
            for process in self.ready_queue:
                if process.priority < smallest_priority.priority:
                    smallest_priority = process
            # self.print(smallest_priority.pid)
            return smallest_priority

        elif self.scheduling_algorithm == "RR": 
            """
            running is:  x 
            An example: ready_queue (a, b, c)
            push to the back (a , b, c, x)
            then pop_left (b, c, x)
            returns a. 
            """
            self.current_process_run_time = 0
            # self.ready_queue.append(self.running) this is done at interupt function
            return self.ready_queue.popleft()
        


    # This method is triggered when the currently running process requests to initialize a new semaphore.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_init_semaphore(self, semaphore_id: int, initial_value: int):
        self.sem_list.append(Semophor(semaphore_id, initial_value, self.running.pid))
        return

    def get_sem(self, semaphor_id):
        for sem in self.sem_list:
            if sem.id == semaphor_id:
                return sem
        raise Exception(f"No semohpor found for {semaphor_id} running process {self.running.pid}")


    # This method is triggered when the currently running process calls p() on an existing semaphore.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_semaphore_p(self, semaphore_id: int) -> PID:
        sem = self.get_sem(semaphore_id)     
        sem.acquire(self.running.pid)
        return self.running.pid

    # This method is triggered when the currently running process calls v() on an existing semaphore.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_semaphore_v(self, semaphore_id: int) -> PID:
        sem = self.get_sem(semaphore_id)
        sem.release(self.running.pid)
        return self.running.pid

    # This method is triggered when the currently running process requests to initialize a new mutex.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_init_mutex(self, mutex_id: int):
        self.mutex_list.append(Mutex(mutex_id))
        return

    def get_mutex(self, mutex_id):
        for mut in self.mutex_list:
            if mut.id == mutex_id:
                return mut
        raise Exception(f"No mutex found for {mutex_id} running process {self.running.pid}")

    
    def new_waiting(self, mutex_id):
        if mutex_id in self.waiting_queue:
            self.waiting_queue[mutex_id].append(self.running)
        else:
            self.waiting_queue[mutex_id] = [self.running]
    
    def less_waiting(self, mutex):
        if self.scheduling_algorithm == "RR":
            sorter = []
            for pcb in self.waiting_queue[mutex.id]:
                sorter.append(pcb)
            sorter.sort(key=lambda x: x.pid)
            self.ready_queue.append(sorter[0])
            mutex.lock(sorter[0])
            self.waiting_queue[mutex.id].remove(sorter[0])

        elif self.scheduling_algorithm == "Priority":
            sorter = []
            for pcb in self.waiting_queue[mutex.id]:
                sorter.append(pcb)
            sorter.sort(key=lambda x: x.priority)
            self.ready_queue.append(sorter[0])
            mutex.lock(sorter[0])
            self.waiting_queue[mutex.id].remove(sorter[0])
            self.running = self.choose_next_process()
    

    # This method is triggered when the currently running process calls lock() on an existing mutex.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_mutex_lock(self, mutex_id: int) -> PID:
        mutex = self.get_mutex(mutex_id)
        if mutex.is_locked():
            self.new_waiting(mutex_id)
            if self.scheduling_algorithm == "Priority" and self.running in self.ready_queue: self.ready_queue.remove(self.running)
            self.running = self.choose_next_process()
            return self.running.pid
        else: # is free to use so update accoringly 
            mutex.lock(self.running)
            return mutex.owner.pid


    # This method is triggered when the currently running process calls unlock() on an existing mutex.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def syscall_mutex_unlock(self, mutex_id: int) -> PID:
        mutex = self.get_mutex(mutex_id)
        #self.logger.log(f'{mutex_id} is locked {mutex.is_locked()}')
        if mutex.is_locked():
            mutex.unlock(self.running)
            if mutex_id in self.waiting_queue and len(self.waiting_queue[mutex_id]) > 0:
                self.less_waiting(mutex)
        return self.running.pid

    # This function represents the hardware timer interrupt.
    # It is triggered every 10 microseconds and is the only way a kernel can track passing time.
    # Do not use real time to track how much time has passed as time is simulated.
    # DO NOT rename or delete this method. DO NOT change its arguments.
    def timer_interrupt(self) -> PID:
        #self.print("rueghiu")
        if self.scheduling_algorithm == "Multilevel":
            self.ml_runtime += 10

            fg_running, bg_running = self.fg.running.pid, self.bg.running.pid
            if self.level == "fg": fg_running = self.fg.timer_interrupt()
            #elif self.level == "bg": bg_running = self.bg.timer_interrupt()

            if fg_running == bg_running == 0: # If nothing is running at all multilevel runtime stays at 0
                self.ml_runtime = 0

            if self.ml_runtime >= 200:
                self.ml_runtime = 0
                if self.level == "fg" and (self.bg.running is not self.bg.idle_pcb or len(self.bg.ready_queue) != 0):
                    #self.logger.log("switched to bg")
                    self.level = "bg"
                    return self.bg.running.pid
                elif self.level == "bg" and (self.fg.running is not self.fg.idle_pcb or len(self.fg.ready_queue) != 0):
                    #self.logger.log("switched to fg")
                    self.level = "fg"
                    return self.fg.running.pid
            
            if self.level == "fg": return fg_running
            elif self.level == "bg": return bg_running

        elif self.scheduling_algorithm == "RR":
            self.current_process_run_time += 10
            if self.current_process_run_time >= 40:
                self.ready_queue.append(self.running)
                self.running = self.choose_next_process()
            return self.running.pid
        
        elif self.scheduling_algorithm == "Priority":
            return self.running.pid
        


class Semophor:
    class EmptySemophor(Exception):
        message: str
        def __init__(self, program, id):
            self.message = f'{program} tried to accuire a semophor with id: {id} but it is empty'
            super().__init__(self.message)
    id = int
    size: int
    program_list: list

    def __init__(self, id, size):
        self.program_list = []
        self.id = id
        self.size = size

    def is_empty(self):
        return self.size != 0
    
    def is_owner(self, program):
        return True if program in self.program_list else False
    
    def acquire(self, program):
        if self.is_empty():
            raise self.EmptySemophor(program)
        self.programs.append(program, self.id)
        self.size -= 1

    
    
    def release(self, program):
        if self.is_owner(program):
            self.program_list.remove(program)
            self.size += 1
        
    

class Mutex:

    class InvalidOwnership(Exception):
        message: str
        def __init__(self, given_program, owner):
            self.message = f'{given_program} is not recongized as the owner. Which is {owner}'
            super().__init__(self.message)

    owner: PCB
    locked: bool
    idle_pcb: PCB
    def __init__(self, id, locked = False):
        self.id = id
        self.idle_pcb = PCB(0)
        self.owner = PCB(0) # no owner default
        self.locked = locked
        

    def is_owner(self, program):
        # if self.owner == idle_pcb then there is no owner
        return self.owner.pid == program.pid or self.owner == self.idle_pcb

    def is_locked(self):
        return self.locked
    
    def lock(self, program) -> PID:
        if not self.is_locked():
            self.owner.pid = program.pid
            self.locked = True
        return self.owner
    
    def unlock(self, program):
        if self.is_owner(program):
            self.owner = self.idle_pcb
            self.locked = False
        # else:
        #     raise self.InvalidOwnership(program, self.owner)