# CS6381_Adversarial_Distributed_Machine_Learning

This package is built for CS6381 Distributed Systems (Vanderbilt) final project, constructed for adversarial distirbuted machine learning.
## Collaborators
Ran Hao (rxh349@case.edu)  Tong Liang (liangtong39@gmail.com) Xiaodong Yang (xiaodong.yang@vanderbilt.edu)

- Please contact us if there is any problem

## Dependencies
- ZeroMQ: http://zeromq.org/
- Java: sudo add-apt-repository ppa:webupd8team/java ; sudo apt update ; sudo apt install oracle-java9-installer ;  sudo apt-get install openjdk-9-jre-headless
- Zookeeper: Download the Zookeeper package from official website: http://www.gtlib.gatech.edu/pub/apache/zookeeper/ ; Uncompress: tar xvzf zookeeper-'version'.tar.gz
- Kazoo: pip install Kazoo
- Pandas: sudo pip install pandas
- Scikit-learn: sudo pip install scikit-learn

## Before running any nodes:
- First go to the zookeeper directory and `cd /bin` then run the zookeeper servers by : `./zkServer.sh start`

## Run one batch of worker nodes:
- Go to the package directory
- `chmod +x worker_batch.sh`
- `./worker_batch.sh scheduler_id`
This will run the scheduler and its corresponding worker nodes.

## Run server node:
- Go to the package directory
- `python server_node.py`

## Run individual worker node:
Each worker node belongs to a mini-batch, where a scheduler is in charger of noticing the server node of the liveness of the worker
- Go to the package directory
- `python worker_node.py "worker_id" "port(default 5560)" "scheduler_id"`

## Run individual scheduler node:
- Go to the package directory
- `python scheduler.py "scheduler_id"`


