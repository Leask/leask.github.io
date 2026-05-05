---
layout: post
title: 'AI is Changing Software Development'
author: Leask
date: '2024-06-23 22:47:00 -0400'
---

![](/assets/img/2024/06/754132945200103424_0.jpg)

// Created by [@leaskh](https://tmblr.co/MMc3t8S0I-DJyxeO4x2p57A) with DALL-E.

I helped my friend write an AI system for processing documents. One part of it is to process the original document as the basis for the next prompt. Previously, we used Google OCR after comparing many OCR tools. I spent some time over the weekend changing it to preprocess through OpenCV and then extracting information using multimodal AI. Ah! It’s so much better than traditional tool chains. The results are tearfully good. The following two images show a comparison of processing the same IELTS score report (sample).

OCR vs Multimodal AI:

![](/assets/img/2024/06/754132945200103424_1.png)![](/assets/img/2024/06/754132945200103424_2.png)

After AI transformation, it can produce relatively controllable outputs through prompt engineering. For example, whether to keep the original text or simplify it, remove unnecessary information such as headers, footers, watermarks, etc., and purposefully simplify and abstract based on context. It can also modify errors and writing in the original text. If traditional OCR is used, due to the mechanical nature of the scanning process, even applying an LLM makes it difficult to correct data relationships that have already been lost previously, such as complex tables and charts in a scene.

The transformation of software development by AI not only involves the user interface that users directly interact with, but also has many possibilities for innovative toolchain-level improvements. These optimizations can greatly enhance the usability of productivity tools, reduce the workload for users to process information in later stages, and alleviate the fatigue of controlling precision in repetitive work. I think this applies equally to language models (LLM) and image models. More subtle improvements will be widespread.

In the visible future, even if it is not a software aimed at AI, benefiting from the introduction of large-scale system-level AI small models, runtime-level integration will make this kind of optimization simpler and all software will become smarter than they are now. This point is completely foreseeable and has already happened on the way.
