import covert_channel
import random

PSK = "Very Secret Pre-Shared Key"
bases = [random.getrandbits(1) for i in range(2048)]


channel1 = covert_channel.CovertStateMachine(PSK, 7)
channel2 = covert_channel.CovertStateMachine(PSK, 7)

print("Channel 1 Trigger: " + str(channel1.trigger))
print("Channel 2 Trigger: " + str(channel2.trigger))

counter = 0
for i in range(len(bases)):
    channel1_result = channel1.feed(bases[i])
    channel2_result = channel2.feed(bases[i])
    if channel1_result and channel2_result:
        print("Match")
        counter += 1

print(counter)


