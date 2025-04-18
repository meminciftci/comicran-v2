## Live Migration:
Seamless live migration is the aim. It means the end user does not notice the downtime caused by the migration procedure. Downtime is the amount of time the process needs to be copied from the VM to destination machine. There are two types of live migration: pre-copy memory migration and post-copy memory migration.

**Pre-copy Migration:** Consists of two phases: pre-copy phase and stop-and-copy phase. In pre-copy phase, memory pages are copied with dirty pages copied again and again. If they still exists, they will be copied on stop-and-copy phase. This phase introduces downtime. 

**Post-copy Migration:** After suspending the source VM, small subset of execution state is transferred to target. The VM is resumed at the target. While it is resuming, remaining memory pages are pushed to the target with respect to the page-faults(network faults). Too many of them degrade the performance of the application. Memory access patern determines the network faults. Pre-paging schema is important to mask network faults. 

**Pre vs Post:** Post copy sends each memory page exactly once whereas pre copy could send them multiple times depending on dirtiness. Pre copy provides up-to-date state of the source VM while post-copy splits the state of the source VM. If the destination fails during live migration, pre-copy recovers, while post-copy cannot. 

## Cloud-RAN:
Clean, Centralized processing, Collaborative radio, and a real-time Cloud Radio Access Network.
**Limitations of Traditional Cellular Architectures**
1. BTS(base stations) are costly to build and operate. 
2. Interference among BTS is more severe as the number of them increases. The same frequencies are being used in the neighboring cells.
3. Users are mobile. Therefore, resources are needed to be maximum at each base station. Waste of processing resources.

**Distinction of C-RAN**
1. Large scale centralized deployment: Allows many RRHs to connect to a centralized BBU pool.
2. Native support to Collaborative Radio technologies: Any BBU can talk with any other BBU within the BBU pool with very high bandwidth (10 Gbit/s and above) and low latency (10 μs level). 
3. Real time virtualization capability: A C-RAN BBU pool is built on open hardware, like x86/ARM CPU based servers, and interface cards that handle fiber links to RRHs and inter-connections in the pool. Real-time virtualization ensures that resources in the pool can be allocated dynamically to base station software stacks, say 4G/3G/2G function modules from different vendors, according to network load. However, to satisfy the strict timing requirements of wireless communication systems, the real-time performance for C-RAN is at the level of tens of microseconds, which is two orders of magnitude better than the millisecond level 'real-time' performance usually seen in Cloud Computing environments.

## Migrating Server Processes: 


## Custom Containarization / Sandboxing Tool:

## Migration Protocol: 

## Stateful Server Programs:

## Stateless Server Programs:

