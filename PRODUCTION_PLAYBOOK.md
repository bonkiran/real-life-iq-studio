# Universal Video Production Playbook

This playbook applies to **REAL-LIFE IQ, Wisdom of Epics, and every future channel/video** unless a channel-specific standard is stricter.

The goal is simple: the user should be reviewing creative choices, not catching basic production defects.

## Standard production order

Research → problem/trigger → narration → storyboard → continuity → slide generation + internal QA → voice QA → final video assembly → viewer playback QA → final render integrity QA → upload package → status update.

Do not skip ahead unless the exception is explicitly documented.

## The 12 checkpoints

### 1. Story Lock Before Generation
Research the topic, define the problem/trigger, lock the narration intent, and approve the shot-by-shot storyboard before final image generation starts.

**Required evidence:** approved story arc + storyboard/shot list.

### 2. Continuity Sheet
Lock the main character, wardrobe, vehicle/device, key props, location, lighting, branding treatment, and emotional progression.

**Required evidence:** one continuity specification used across every slide.

### 3. Physical-Reality Test
Before approving any shot, verify that screens, mirrors, hands, vehicles, bags, furniture, devices, body positions, and camera viewpoints behave as they would in the real world.

Examples:
- A phone or laptop screen should face the person using it unless the viewer sees a separate POV/inset.
- A driver-side mirror should be oriented for the driver, not conveniently toward the viewer.
- Vehicles must have complete, realistic geometry.
- Hands must interact naturally with props.
- No floating logos, impossible props, duplicated limbs, or unexplained UI.

### 4. Cinematic Storytelling
Use sequential real-world actions and visual cause/effect rather than static informational posters.

A viewer should largely understand the story with the audio muted.

### 5. Batch Generation + Internal Correction
Generate in manageable batches. Inspect internally and redo obvious failures before presenting slides for review.

The user should not be the first person to catch malformed cars, impossible anatomy, wrong screen orientation, duplicated people, random props, or continuity breaks.

### 6. Fixed Visual QC Gate
No slide is ready until it passes:
- correct aspect ratio
- realistic anatomy
- realistic object geometry
- correct physical perspective
- consistent character
- consistent props
- appropriate branding
- no floating logo
- no distracting posters/books/background wording
- limited, purposeful text
- no neighboring-slide remnants or bleed
- visual matches narration

For Shorts, default to **true full-frame 9:16 HD, 1080×1920**.

No slide numbering or `#` labels unless the creative concept explicitly requires them.

If a mug/tumbler naturally belongs in the scene, the channel logo must be physically printed on it. The character should not present or point at it unless the video is actually about that object.

### 7. Separate Slide / Voice / Video Validation
Never use a generic `tested` label.

**Slide QA** checks realism, continuity, composition, text, props, aspect ratio, and narration match.

**Voice QA** checks complete narration, correct sequence, intelligibility, duration, and distortion.

**Video QA** checks the actual rendered frames, not just MP4 metadata: full-frame 9:16, audio presence, narration/slide alignment, transition boundaries, no bleed, complete decode, and final duration.

### 8. Visual Pacing
Do not force a long narration block onto one slide.

For Shorts, target a meaningful visual change roughly every **3–5 seconds** when the story supports it. Longer holds require an intentional reason.

Motion must be intentional. Do not use bounce, zoom-settle-bounce, repeated Ken Burns motion, or other decorative animation that distracts from the story.

### 9. Reusable Approved Shot Library
Build and reuse approved scene patterns for recurring situations such as:
- driving / rear-view awareness
- bank / ATM
- gas station
- parking lot
- café / retail stop
- police station
- home office
- device recovery
- stolen purse / wallet
- airport / public transit

Reuse the composition logic while adapting the character and story.

### 10. End-to-End Pipeline Discipline
Do not begin a downstream production stage until its prerequisite is approved, unless the exception is documented.

Every video must be updated in the living QC tracker against all checkpoints.

### 11. Viewer Playback Validation
Watch the **complete final rendered video from start to finish exactly like a viewer would** before sending it for approval.

The narration is the master timeline. Confirm:
- every spoken sentence has the correct visual
- no visual appears too early or too late
- no wrong slide is shown for the narration
- no slide is repeated unintentionally
- no bounce or unnecessary motion remains
- transitions feel natural
- the ending progresses rather than repeating a prior visual
- the story remains coherent from beginning to end

A contact sheet, transition sampling, metadata check, or partial preview does **not** replace this full playback review.

**Required evidence:** full-playback pass/fail result plus timestamps for every defect found and corrected.

### 12. Final Render Integrity
Validate the **actual MP4 that will be delivered to the user**, after the final render is complete.

Confirm:
- true full-frame 9:16
- 1080×1920 for Shorts unless explicitly requested otherwise
- correct first and last frame
- no black bars or unintended cropping
- no duplicated visual segments
- no bounce / animation artifacts
- correct transition behavior
- audio present throughout
- slide-to-voice synchronization
- full decode succeeds without errors

**Required evidence:** final render checklist, technical media properties, and visual spot checks of the delivered file.

## Definition of `tested and validated`

Do **not** say an artifact is tested and validated unless the relevant QA evidence exists.

A technically valid MP4 is not enough if the visible content is letterboxed, misaligned, unrealistic, repeated, bouncing, missing audio, out of sync, or contains slide bleed.

A video cannot be marked **READY** until CP11 Viewer Playback Validation and CP12 Final Render Integrity both pass on the exact file being sent for approval.

## Production Control Tower

Every active video must expose a visible status summary containing:
- current stage
- completion percentage
- last completed activity
- current activity
- next gate
- blockers
- last updated timestamp

If no active execution is occurring, say so explicitly. Do not imply background work is continuing when it is not.

## Living tracker

The master spreadsheet is:

`Universal_Video_Production_QC_Living_Tracker.xlsx`

For each video, record the status of all 12 checkpoints and the evidence/fix notes. Historical videos should not be retroactively claimed as compliant unless they are actually reviewed against this playbook.
