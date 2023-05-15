#!/usr/bin/env python
import rospy
import importlib

import sys
#https://answers.ros.org/question/256251/how-to-obtain-list-of-all-available-topics-python/
#https://answers.ros.org/question/36855/is-there-a-way-to-subscribe-to-a-topic-without-setting-the-type/
#http://schulz-m.github.io/2016/07/18/rospy-subscribe-to-any-msg-type/

import rosgraph
import rostopic

from prometheus_client import start_http_server, Counter

def get_topics():
    master = rosgraph.Master('/rostopic')
    pubs, subs = rostopic.get_topic_list(master=master)

    # not sure if any better or different that master=None
    master = rosgraph.Master('/rostopic')
    pubs, subs = rostopic.get_topic_list(master=master)
    topic_data = {}
    print(f"pubs {len(subs)}")
    for topic in pubs:
        name = topic[0]
        if name not in topic_data:
            topic_data[name] = {}
            topic_data[name]['type'] = topic[1]
        topic_data[name]['publishers'] = topic[2]

    print(f"subs {len(pubs)}")
    for topic in subs:
        name = topic[0]
        if name not in topic_data:
            topic_data[name] = {}
            topic_data[name]['type'] = topic[1]
        topic_data[name]['subscribers'] = topic[2]


    #for topic_name, val in sorted(topic_data.items()):
    #    print(topic_name, ': ', val)

    return topic_data

class GenericMessageSubscriber():
    def __init__(self, topic_name, callback):
        self._binary_sub = rospy.Subscriber(
            topic_name, rospy.AnyMsg, self.generic_message_callback)
        self._callback = callback

    def generic_message_callback(self, data):
        assert sys.version_info >= (2,7) #import_module's syntax needs 2.7
        connection_header =  data._connection_header['type'].split('/')
        ros_pkg = connection_header[0] + '.msg'
        msg_type = connection_header[1]
        msg_class = getattr(importlib.import_module(ros_pkg), msg_type)
        msg = msg_class().deserialize(data._buff)
        self._callback(msg)

def gen_mesage_callback(counter):
    def message_callback(data):
        # handle your callback exactly as you would do it with a normal Subscriber
        print('incing')
        counter.inc()

    return message_callback

def sub_topics(topics, counters):

    subs = []

    for topic_name, pub_subs in topics.items():
        
        safe_topic_name = topic_name.replace('/', '_')

        if not safe_topic_name in counters.keys():
            print ('establishing counter: ', safe_topic_name)
            c = Counter(safe_topic_name, 'msg count')
            counters.update({safe_topic_name: c})
        else:
            c = counters[safe_topic_name]

        sub = GenericMessageSubscriber(topic_name, gen_mesage_callback(c))
        subs.append(sub)

    return subs, counters

if __name__ == '__main__':


    start_http_server(8000)
    # In ROS, nodes are uniquely named. If two nodes with the same
    # name are launched, the previous one is kicked off. The
    # anonymous=True flag means that rospy will choose a unique
    # name for our 'listener' node so that multiple listeners can
    # run simultaneously.
    rospy.init_node('generic_listener', anonymous=True)

    counters = dict()

    # spin() simply keeps python from exiting until this node is stopped
    while not rospy.is_shutdown():
        topics = get_topics()
        subs, counters = sub_topics(topics, counters)

        rospy.sleep(10.0)