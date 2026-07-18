---
title: "I got tired of changing batteries"
date: 2026-04-13T15:07:25-07:00
lastmod: 2026-04-13T15:28:00-07:00
description: "I have a Schlage Encode Plus Smart Wi-Fi Lock for Front Door. It’s a very usable door lock with many modern features. It takes a small battery pack that contains 4 AA batteries. This is fine. Unfortunately, the failure mode"
tags: ["battery", "DIY", "door lock", "home automation", "Schlage", "UPS"]
categories: ["IoT", "Tech"]
draft: false
slug: "i-got-tired-of-changing-batteries"
---
I have a [Schlage Encode Plus Smart Wi-Fi Lock for Front Door](https://www.amazon.com/dp/B09RS3W7M5?ref_=ppx_hzsearch_conn_dt_b_fed_asin_title_1).

{{< figure src="/images/schlage_doorlock.png" >}}

It’s a very usable door lock with many modern features. It takes a small battery pack that contains 4 AA batteries. This is fine.

{{< figure src="/images/thisisfine.png" >}}

Unfortunately, the failure mode for the batteries being dead is unpleasant.  So, obviously, the best thing to do is to constantly check and change out the batteries before things go wrong.

You cannot win here.  Eventually, you will suffer.

So, I decided to get out of the business of even caring about changing batteries and completely over-engineer a solution that satisfies my goals.

Goal #1: Line power

Goal #2: UPS based on line power

Goal #3: Never change batteries again

Turns out, it’s pretty easy to make this work.

I removed the battery pack completely and McGuyvered a single wire per contact in the unit. I ended up just looping wire underneath the “inverted-V” of the battery pack contact and then just twisted it around itself several times to secure it.  Positive is on the right side (when looking at the back of the door lock. Negative on the left.

After that, I just used a couple of wire nuts and one of these beauties: [USB C to 2 Pin Bare Wire Open End Power Cable](https://www.amazon.com/dp/B0DLKPWF1G?ref=ppx_yo2ov_dt_b_fed_asin_title&th=1). I also needed a nice USB-C extension cord to make the distance, but it worked great. $17.06.

So, now I just needed to power this USB-C pigtail with some UPC power. So, I got this: [SKE DC20000 Plus Altair – Mini DC UPS](https://www.amazon.com/dp/B0CQR5GMN4?ref=ppx_yo2ov_dt_b_fed_asin_title). $71.68.

Plugged in the UPS to a wall socket and *Voilà!*

Line power + UPS + USB-A to C adapter + USB-C extension cable + USB-C pigtail + McGuyvering ==> RESULT!!

{{< figure src="/images/img_9163.jpg" caption="Wire loops around contacts (at the bottom of the battery pack cavity)" >}}

{{< figure src="/images/img_9164.jpg" caption="Wire loops connected with wire nuts to USB-C pigtail" >}}

{{< figure src="/images/img_9165.jpg" caption="USB-C extension connected to UPS using USB-A (why!?!)" >}}

For reasons that are unclear, I was unable to use the USB-C port on the UPS, so I just put in a C-to-A adapter and used the USB-A port instead.

The Schlage iOS app thinks the battery level is 32%, but since that never changes, I’m totally fine with that.

You too can spend money to solve a problem that is only a minor irritation. Good luck and may the force be with you.
