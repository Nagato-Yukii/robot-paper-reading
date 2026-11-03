# NOTICE

This repository contains **bilingual reading notes** for robotics papers.

- The source text (English or Chinese), figures, tables, and original PDFs
  belong to their respective authors. Source excerpts and cropped images are
  retained here for study, translation, and commentary. Original titles and
  local-source provenance are recorded in `content/library-manifest.json`.
- The Chinese translations, site templates, and code in `pipeline/` are
  released under the repository MIT license, except translations derived from
  CC BY 4.0 papers listed below, whose attribution and license must be retained. The Chinese source article
  remains its original author's work and is not a new translation.

Included papers:

1. *Scaling Online Exploration for Robot Agents* — Runhan Huang et al.
2. *Bundled Contact Gradients: Stabilizing Differentiable Simulation for
   Deployable Dynamic Tasks* — Dyuman Aditya et al. (arXiv:2609.30951)

Imported library (29 English papers translated or polished with Gemini 3.8 Flash Medium
and one original Chinese article):

3. *Adversarial Locomotion and Motion Imitation for Humanoid Policy Learning*
4. *Track Any Motions under Any Disturbances*
5. *ASAP: Aligning Simulation and Real-World Physics for Learning Agile Humanoid Whole-Body Skills*
6. *ASE: Large-Scale Reusable Adversarial Skill Embeddings for Physically Simulated Characters*
7. *BeyondMimic: From Motion Tracking to Versatile Humanoid Control via Guided Diffusion*
8. *Towards bridging the gap: Systematic sim-to-real transfer for diverse legged robots*
9. *A Reduction of Imitation Learning and Structured Prediction to No-Regret Online Learning*
10. *DreamWaQ: Learning Robust Quadrupedal Locomotion With Implicit Terrain Imagination via Deep Reinforcement Learning*
11. *Expressive Whole-Body Control for Humanoid Robots*
12. *World-Grounded Human Motion Recovery via Gravity-View Coordinates*
13. *Learning H-Infinity Locomotion Control*
14. *Hiking in the Wild: A Scalable Perceptive Parkour Framework for Humanoids*
15. *Hybrid Internal Model: Learning Agile Legged Locomotion with Simulated Robot Response*
16. *KungfuBot: Physics-Based Humanoid Whole-Body Control for Learning Highly-Dynamic Skills*
17. *KungfuBot2: Learning Versatile Motion Skills for Humanoid Whole-Body Control*
18. *Learning From Failures: Efficient Reinforcement Learning Control with Episodic Memory*
19. *LSWM: A Long–Short History World Model for Bipedal Locomotion via Reinforcement Learning*
20. *机器人强化学习与关节PD控制 - 知乎*
21. *Robust Humanoid Walking on Compliant and Uneven Terrain with Deep Reinforcement Learning*
22. *RT-1: Robotics Transformer for Real-World Control at Scale*
23. *VisualMimic: Visual Humanoid Loco-Manipulation via Motion Tracking and Generation*
24. *RT-2: Vision-Language-Action Models Transfer Web Knowledge to Robotic Control*
25. *WHAM: World-grounded Humans with Accurate Motion*
26. *ZEST: Zero-shot Embodied Skill Transfer for Athletic Robot Control*
27. *Blind Precise Assembly: Proprioceptive Sim-to-Real Peg-in-Hole for Diverse Parts* — Antonia Bronars, Younghyo Park, Kushal Kedia, Pulkit Agrawal (arXiv:2610.23849)

28. *Blind Dexterity: Whole-Body Humanoid Manipulation via Pure Proprioception* — Aditya Bhatt, Oleg Kaidanov, Puze Liu, Jan Peters (arXiv:2608.29487)

29. *Minimizing Energy Consumption Leads to the Emergence of Gaits in Legged Robots* — Zipeng Fu, Ashish Kumar, Jitendra Malik, Deepak Pathak. PMLR 164:928–937, 2022 (CoRL 2021). [Original publication](https://proceedings.mlr.press/v164/fu22a.html). [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Chinese machine translation and reading layout added by this project using Gemini 3.8 Flash Medium.

30. *Adaptive Energy Regularization for Autonomous Gait Transition and Energy-Efficient Quadruped Locomotion* — Boyuan Liang, Lingfeng Sun, Xinghao Zhu, Bike Zhang, Ziyin Xiong, Yixiao Wang, Chenran Li, Koushil Sreenath, Masayoshi Tomizuka. 2403.20001v2. [Original publication](https://arxiv.org/abs/2403.20001). [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Chinese machine translation and reading layout added by this project using Gemini 3.8 Flash Medium.

31. *The Duke Humanoid: Design and Control For Energy Efficient Bipedal Locomotion Using Passive Dynamics* — Boxi Xia, Bokuan Li, Jacob Lee, Michael Scutari, Boyuan Chen. 2409.19795v2. [Original publication](https://arxiv.org/abs/2409.19795). [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Chinese machine translation and reading layout added by this project using Gemini 3.8 Flash Medium.

32. *ECO: Energy-Constrained Optimization with Reinforcement Learning for Humanoid Walking* — Weidong Huang, Jingwen Zhang, Jiongye Li, Shibowen Zhang, Jiayang Wu, Jiayi Wang, Hangxin Liu, Yaodong Yang, Yao Su. 2602.06445v1. [Original publication](https://arxiv.org/abs/2602.06445). [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Chinese machine translation and reading layout added by this project using Gemini 3.8 Flash Medium.

Energy & Gaits: Proceedings of the 5th Conference on Robot Learning, PMLR 164:928–937, 2022. [PMLR publication license](https://proceedings.mlr.press/pmlr-license-agreement.html).

If you are an author and would like your paper, its figures, or its PDF
removed from this repository, please open an issue and it will be removed
promptly.

Translation status: RAX and BCG are curated reading pages. The imported
English library has been polished paragraph by paragraph against the source
English through the local Antigravity CLI using gemini-3.8-flash-medium with
medium effort. It has not been reviewed paragraph by paragraph by a human.
Per-paper polish_provenance.json records model requests, successful batch
sessions, output checksums, and token usage. Original formulas, diagrams,
and source crops remain available for verification. Where wording differs,
consult the original paper. The Chinese source article is unchanged.

## GAE and PPO additions

- *High-Dimensional Continuous Control Using Generalized Advantage Estimation* — John Schulman, Philipp Moritz, Sergey Levine, Michael I. Jordan, Pieter Abbeel. ICLR 2016; arXiv:1506.02438v6. [Original](https://arxiv.org/abs/1506.02438).
- *Proximal Policy Optimization Algorithms* — John Schulman, Filip Wolski, Prafulla Dhariwal, Alec Radford, Oleg Klimov. arXiv:1707.06347v2, 2017. [Original](https://arxiv.org/abs/1707.06347).

Original papers and figures remain attributed to their respective authors and rights holders. Chinese translations were generated using GPT-6 Astra High, with original numbered equations and figures retained for reference. These translations have not been fully reviewed by a human.

## ControlVAE, SuperTrack and Dreamer additions

- *ControlVAE: Model-Based Learning of Generative Controllers for Physics-Based Characters* — Heyuan Yao, Zhenhua Song, Baoquan Chen, Libin Liu. SIGGRAPH Asia 2022; 2210.06063v1. [Original](https://arxiv.org/abs/2210.06063).
- *SuperTrack: Motion Tracking for Physically Simulated Characters using Supervised Learning* — Levi Fussell, Kevin Bergamin, Daniel Holden. SIGGRAPH Asia 2021; Author version, September 2021. [Original](https://doi.org/10.1145/3478513.3480527).
- *Dream to Control: Learning Behaviors by Latent Imagination* — Danijar Hafner, Timothy Lillicrap, Jimmy Ba, Mohammad Norouzi. ICLR 2020; 1912.01603v3. [Original](https://arxiv.org/abs/1912.01603).

Original papers, notices, equations and figures remain attributed to their respective authors and rights holders. Chinese translations were generated using GPT-6 Astra High and have not been fully reviewed by a human. Author PDFs retain their original rights notices; inclusion here does not change their licenses.

## Active Inference: A Process Theory

Karl Friston, Thomas FitzGerald, Francesco Rigoli, Philipp Schwartenbeck, Giovanni Pezzulo. *Active Inference: A Process Theory*. Neural Computation 29(1):1–49, 2017. [Original DOI](https://doi.org/10.1162/NECO_a_00912). Original copyright notice: © 2016 Massachusetts Institute of Technology. The PDF was supplied locally by the user for personal study; it includes an additional later citing-article list. Chinese translation generated using Gemini 3.8 Flash Medium, awaiting human review. Original figures, equations and notices remain attributed to the rights holders; no license change is asserted.
