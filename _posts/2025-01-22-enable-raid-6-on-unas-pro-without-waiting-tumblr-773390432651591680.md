---
layout: post
title: 'Enable RAID 6 on UNAS Pro without waiting'
author: Leask
date: '2025-01-22 11:16:00 -0500'
---

I’ve had the UNAS for a few weeks, and before receiving it, I was concerned about the lack of RAID 5 support on the UNAS Pro. However, RAID 6 protection is crucial for my stored data. As a long-time mdadm user, and knowing that UNAS also utilizes it, I was confident in my ability to resolve this issue independently. Given mdadm’s robust support for array modification and migration, I believed that directly expanding the array using the `grow` command would address the problem.

You can start with any RAID configuration because `mdadm` allows for lossless migration from RAID 0, RAID 1, and RAID 5 to RAID 6. Specific migration constraints exist, but a simple calculation can provide a rough verification, though you should always consider your array’s specific situation. Generally, migration is feasible if the resulting array’s usable capacity is equal to or greater than the current usable capacity. If the migration results in reduced disk capacity, such as when upgrading from RAID 5 to RAID 6 without adding disks or utilizing a hot spare disk, you’ll need to shrink the storage partition beforehand. This involves moving data to the front of the disk and trimming the unused space, which can be achieved using `resize2fs`. However, this is beyond the scope of this discussion.

Most UNAS users likely have RAID 5 configured. If a hot spare disk was previously designated, upgrading to RAID 6 using that hot spare is the simplest, quickest, and safest method. This process is also straightforward if an empty drive bay is available on your UNAS. However, if no spare disks or bays are available, reducing partition size and removing a disk before migrating will be required.

For example, I previously used RAID 5 with all disks utilized. I had reduced the partition volume and added a hot spare disk. I then executed the following command to upgrade:

> mdadm –grow /dev/md3 –level=6 –raid-devices=7

Please note that the upgrade is required for md3. md0 is reserved for other system metadata storage. You can use the command `watch cat /proc/mdstat` in the terminal to monitor the disk synchronization progress. Once synchronization is complete, you will see the following information.

> root@UNAS-Pro:~# cat /proc/mdstat  
> Personalities : [linear] [raid0] [raid1] [raid6] [raid5] [raid4] [raid10]  
> md0 : active raid1 sdg2[0] sdb2[6] sda2[5] sdd2[4] sdf2[3] sdc2[2] sde2[1]  
> 1961984 blocks super 1.2 [7/7] [UUUUUUU]  
> md3 : active raid6 sdg5[0] sdb5[6] sda5[5] sdd5[4] sdf5[3] sdc5[2] sde5[1]  
> 58551802880 blocks super 1.2 level 6, 512k chunk, algorithm 2 [7/7] [UUUUUUU]  
> bitmap: 0/6 pages [0KB], 65536KB chunk  
> unused devices: &lt;none&gt;

Executing `mdadm –detail /dev/md3` will now show that the array has been completely converted to RAID6.

> root@UNAS-Pro:~# mdadm –detail /dev/md3  
> /dev/md3:  
> Version : 1.2  
> Creation Time : Thu Jan 16 11:33:12 2025  
> Raid Level : raid6  
> Array Size : 58551802880 (55839.35 GiB 59957.05 GB)  
> Used Dev Size : 11710360576 (11167.87 GiB 11991.41 GB)  
> Raid Devices : 7  
> Total Devices : 7  
> Persistence : Superblock is persistent Intent Bitmap : Internal Update Time : Wed Jan 22 10:30:20 2025 State : clean Active Devices : 7  
> Working Devices : 7  
> Failed Devices : 0  
> Spare Devices : 0 Layout : left-symmetric  
> Chunk Size : 512K  
> Consistency Policy : bitmap  
> Name : UNAS-Pro:3 (local to host UNAS-Pro)  
> UUID : e3bde202:cbb13026:be46c779:add176fb  
> Events : 125218  
> Number Major Minor RaidDevice State  
> 0 8 101 0 active sync /dev/sdg5  
> 1 8 69 1 active sync /dev/sde5  
> 2 8 37 2 active sync /dev/sdc5  
> 3 8 85 3 active sync /dev/sdf5  
> 4 8 53 4 active sync /dev/sdd5  
> 5 8 5 5 active sync /dev/sda5  
> 6 8 21 6 active sync /dev/sdb5

Upgrading from version 5 to 6 is generally safe, but please ensure you back up your data beforehand. After waiting approximately a day for the disk to synchronize, all services were running normally and the data remained intact.

At this point, the management interface will still display “Basic Protection” because the UI reflects a configuration file. To proceed, access the UniFi OS terminal and edit the file at `/data/unifi-core/config/settings.yaml`.

> root@UNAS-Pro:~# cat /data/unifi-core/config/settings.yaml  
> anonymous_device_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  
> isInternalUser: false  
> isSetup: true  
> location:  
> lat: xx.111966  
> long: -xxx.0323814  
> radius: 200  
> text: Uranium City, Saskatchewan, Canada  
> name: UNAS Pro  
> timezone: America/Toronto  
> sendDiagnostics: anonymous  
> autoBackupEnabled: true  
> internetRequired: true  
> lcmSettings:  
> enabled: true  
> color: 0139FF  
> brightness: 100  
> ledSettings:  
> enabled: true  
> nightMode:  
> onMinute: 180  
> offMinute: 181  
> owner: null  
> emailServiceProvider: ui  
> ustorage:  
> hotspare: false  
> raid: raid6  
> setup_device_id: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx  
> setupType: ios  
> setupDuration: null  
> country: 124  
> ssh:  
> agreementAcceptedAt: 2025-01-10T19:56:13.116Z  
> agreementAcceptedByUserId: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

The configuration needs to be updated to match the changes made to the mdadm array during migration. For example, I changed the hotspare setting from true to false, and the RAID level from RAID5 to RAID6. You will see these changes reflected in the configuration on the management webpage. If the changes are not updated, reboot the server to see the correct information.

![](/assets/img/2025/01/773390432651591680_0.png)

You can now enjoy using RAID 6 on your UNAS Pro. Actually, there are two ways to access the configuration page on UNAS Pro. One method is through UniFi’s cloud access; however, the “Advanced Protection” setting will not be visible because the UI for UniFi OS 4.1.11 / Drive 1.16.15 is not yet adapted. You can see the correct configuration by accessing via local IP address. This explains why some community members can see this configuration, while others cannot. This issue is expected to be resolved in OS 4.2, but it does not impact functionality.

Additionally, if you are using a 10G connection on your local network, remember to enable jumbo frames for optimal performance. The simplest way to do this is by adding the following to `/etc/crontab`:

> [@reboot](https://tmblr.co/MeB0zht2yd4afHHx6T0symg) root /sbin/ip link set enp0s2 mtu 9000

My local network can essentially run at the full 10Gbps speed.

> root@UNAS-Pro:~# iperf3 -c 192.168.1.204  
> Connecting to host 192.168.1.204, port 5201  
> [ 5] local 192.168.1.64 port 60334 connected to 192.168.1.204 port 5201  
> [ ID] Interval Transfer Bitrate Retr Cwnd  
> [ 5] 0.00-1.00 sec 1.09 GBytes 9.34 Gbits/sec 497 760 KBytes  
> [ 5] 1.00-2.00 sec 1.11 GBytes 9.55 Gbits/sec 804 516 KBytes  
> [ 5] 2.00-3.00 sec 1.09 GBytes 9.40 Gbits/sec 825 341 KBytes  
> [ 5] 3.00-4.00 sec 1.12 GBytes 9.61 Gbits/sec 1030 533 KBytes  
> [ 5] 4.00-5.00 sec 1.10 GBytes 9.49 Gbits/sec 741 428 KBytes  
> [ 5] 5.00-6.00 sec 1.10 GBytes 9.43 Gbits/sec 911 376 KBytes  
> [ 5] 6.00-7.00 sec 1.13 GBytes 9.70 Gbits/sec 789 1.13 MBytes  
> [ 5] 7.00-8.00 sec 1.08 GBytes 9.27 Gbits/sec 790 341 KBytes  
> [ 5] 8.00-9.00 sec 1.10 GBytes 9.49 Gbits/sec 483 568 KBytes  
> [ 5] 9.00-10.00 sec 1.12 GBytes 9.66 Gbits/sec 733 306 KBytes  
> [ ID] Interval Transfer Bitrate Retr  
> [ 5] 0.00-10.00 sec 11.1 GBytes 9.49 Gbits/sec 7603 sender  
> [ 5] 0.00-10.00 sec 11.0 GBytes 9.49 Gbits/sec receiver

Okay, that concludes this discussion. Please feel free to leave comments if you have any questions. As a final reminder, always back up your important data before making any array changes.

*PS: This article was originally published in the UniFi community by me, and the original link can be found here: [https://community.ui.com/questions/Enable-RAID-6-on-UNAS-Pro-without-waiting/8b333b9f-5168-4261-b81a-1eab3c039de7](https://community.ui.com/questions/Enable-RAID-6-on-UNAS-Pro-without-waiting/8b333b9f-5168-4261-b81a-1eab3c039de7) .*
