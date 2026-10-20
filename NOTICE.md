# NOTICE

This repository contains **bilingual reading notes** for robotics papers.

- The source text (English or Chinese), figures, tables, and original PDFs
  belong to their respective authors. Source excerpts and cropped images are
  retained here for study, translation, and commentary. Original titles and
  local-source provenance are recorded in `content/library-manifest.json`.
- The Chinese translations, site templates, and code in `pipeline/` are
  released under the repository MIT license. The Chinese source article
  remains its original author's work and is not a new translation.

Included papers:

1. *Scaling Online Exploration for Robot Agents* — Runhan Huang et al.
2. *Bundled Contact Gradients: Stabilizing Differentiable Simulation for
   Deployable Dynamic Tasks* — Dyuman Aditya et al. (arXiv:2609.30951)

Imported library (23 English papers polished with Gemini 3.8 Flash Medium
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
