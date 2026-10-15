```{=latex}
\begin{titlepage}
\thispagestyle{empty}
\begin{tikzpicture}[remember picture,overlay]
  % 封面绝对定位，坐标 = 距页面左上角 (pt)，版式对齐 LITEARM SE 产品手册封面
  % 封面图与中文版共用 images/ 下的两张 PNG（图本身没有语言）
  \node[anchor=north,inner sep=0pt] at ($(current page.north west)+(298.75pt,-108.9pt)$)
      {\includegraphics[width=100pt,height=112pt,keepaspectratio]{images/cover_litearm_logo.png}};
  \node[anchor=center] at ($(current page.north west)+(298.75pt,-262.4pt)$)
      {{\fontsize{28}{34}\selectfont\bfseries Installation Guide}};
  \node[anchor=north,inner sep=0pt] at ($(current page.north west)+(298.75pt,-300.8pt)$)
      {\includegraphics[width=289.1pt,height=289.1pt,keepaspectratio]{images/cover_litearm_se.png}};
  \node[anchor=center] at ($(current page.north west)+(298.75pt,-717.8pt)$)
      {{\fontsize{11}{14}\selectfont\bfseries NEXFORM ROBOTICS}};
  \node[anchor=center] at ($(current page.north west)+(298.75pt,-747.9pt)$)
      {{\fontsize{9}{13}\selectfont Version 1.0\qquad 13 October 2026}};
\end{tikzpicture}
\end{titlepage}
\pagenumbering{Roman}
\thispagestyle{frontmatter}
\tableofcontents
\clearpage
\pagenumbering{arabic}
```

# Introduction

What does it take to install a robot arm for the first time, such that it is actually assembled and running reliably? For developers, engineers, and robotics enthusiasts who are new to robot arms, the goal of the installation stage is usually not to write code but to get the device assembled safely and firmly, and connected up.

This guide covers the complete hardware installation of the LITEARM-SE, from unpacking and checking the parts through to the electrical connection. Software development and motion tuning are out of scope. Read it before you start, and check the parts against the packing list first.

The order matters: **assemble the arm first, then connect power and cables.** Assembly means turning the arm over, lining up holes, and tightening screws. Do that work before the cables are attached, and no cable gets pulled around during assembly or ends up inside a joint's range of motion.

LITEARM-SE can be installed in either of two ways. Pick the one that matches how you will use it. Both share the same electrical connection procedure:

- **Option 1 | Tabletop mount**: fix the arm to the base plate and clamp the plate to the edge of a table. Use this when the arm stays in one workplace.
- **Option 2 | Column mount**: build a column base from the X-shaped base plate, the feet, the casters, the column, and the top mount, then assemble the arm onto it. Use this when you need to adjust the mounting height, or when you need the teleoperation configuration.

**Keywords**: robot arm installation, unpacking, tabletop mount, column mount, electrical connection

## Installation path

You do **not** need both paths. Decide which mount you are using, then read according to this table: chapters 2 and 5 apply either way, and the only choice is between chapter 3 and chapter 4.

| Chapter | Content | Tabletop mount | Column mount |
| --- | --- | --- | --- |
| 1 | Introduction | Required | Required |
| 2 | Unpacking: check that all parts are present | Required | Required |
| 3 | Tabletop mount: fix the arm to a table | **Required** | Skip |
| 4 | Column mount: build the column base and assemble the arm | Skip | **Required** |
| 5 | Electrical connection: power and communication | Required | Required |
| 6 | Installation notes | Required | Required |

- **Tabletop mount**: read chapters 2, 3, 5, and 6. **Skip chapter 4 entirely.**
- **Column mount**: read chapters 2, 4, 5, and 6. **Skip chapter 3 entirely.**

# Unpacking: check that all parts are present

Before you start, check that the arm and its accessories are all in the box. Packing list:

- Robot arm
- Controller board
- USB cable
- Robot arm power output
- 600 W switching power supply kit (optional)
- Tabletop mount kit (optional)
- Column kit (optional)

Points to watch while you check:

- Check the parts for the mount you chose. For the **tabletop mount**, make sure the tabletop mount kit is complete; for the **column mount**, make sure the column kit is complete.
- The controller board, the USB cable, and the robot arm power output are all used in chapter 5. Keep them together within reach so that the wiring step goes faster.
- Finish the check first, and do not apply power yet.
- If a part is missing or damaged, contact support before you go on. Do not force non-matching parts to fit.

# Tabletop mount: fix the arm to a table

The arm generates inertia and reaction forces as it moves. If the base is not held firmly, the arm can shift it while moving, which costs you stability and can be a safety risk. Fix the base in a stable position before you apply power or test any motion.

The tabletop mount uses the base plate and the G-clamps, and suits a fixed workplace such as a table edge. If you are using the column mount, read chapter 4 instead.

**Step 1**: use the supplied M5 screws to fix the arm to the base plate.

![Arm fixed to the base plate](images-en/fig01-arm-on-base.jpg)

**Step 2**: put the base plate in a suitable position at the edge of the table.

![Base plate at the edge of the table](images-en/fig02-base-on-edge.jpg)

**Step 3**: use the G-clamps to clamp the base plate to the table.

![G-clamps holding the base plate](images-en/fig03-clamp.jpg)

**Step 4**: check that the base plate is held firmly against the table, with no play.

![Base plate clamped in place](images-en/fig04-tabletop-done.jpg)

**Step 5**: use the supplied screws to fix the controller board to the base plate. The tabletop mount is now complete.

![Controller board fixed to the base plate](images-en/fig05-control-board-mount.jpg)

> **Tip**: when you tighten the screws, line all of them up with their holes first and then tighten them in turn. Tightening one screw all the way first shifts the holes and makes the rest hard to line up.

# Column mount: build the column base and assemble the arm

All of the mechanical assembly for the column mount happens in this chapter: first the X-shaped base plate, feet, casters, and column go together into the column base, then the arm goes onto the column, and then the cable is routed inside the column. Steps 1 to 8 run one after another. **Figure 6** shows the assembled result.

![Column assembly](images-en/fig06-column.jpg)

**Step 1**: turn the X-shaped base plate upside down and press the four feet into the M16 holes at its ends.

> **Note**: do not remove the nuts from the feet.

**Step 2**: use the M8 screws with washers to fit the four casters to the underside of the base plate, one after another.

![Fitting the casters](images-en/fig07-feet-casters.jpg)

**Step 3**: turn the base plate over again, now with the feet and casters fitted. Line up the holes in the bottom of the column with the holes in the base plate and fix them with the eight M10 hex screws, washers, and nuts.

![Fitting the column to the base plate](images-en/fig08-column-base.jpg)

**Step 4**: fix the top mount carrying the NEXFORM logo to the top face of the column with the four M6 socket screws.

![Fitting the top mount](images-en/fig09-top-mount.jpg)

With the column base assembled, the arm can go onto the column. There are two configurations and you use **one or the other**: the teleoperation configuration if you need to move the arm by hand (fit the extension piece first, in steps 5 and 6), or direct assembly if you control the arm normally (step 7).

**Step 5**: to move the arm by hand, fit the extension piece first.

**Step 6**: line up the end of the extension piece that has no nut in it with the height you need, and fix it to the part carrying the NEXFORM logo with six M5 screws. Then fix the arm to the extension piece with six more M5 screws.

![Fitting the extension piece](images-en/fig10-extension.jpg)

**Step 7**: to control the arm normally, fix it directly to the column at the height you need with six M5 screws.

![Assembling the arm directly onto the column](images-en/fig11-arm-direct.jpg)

**Step 8**: route the cable inside the column. Use the extension cable to lead the arm's power cable into the column and out through the bottom. The connection after it comes out is described in the next chapter.

![Power cable led into the column through the mount](images-en/fig12-column-routing.jpg)

![Cable exiting below the column](images-en/fig13-cable-exit.jpg)

> **Note**: the side-mount parameters depend on which way each arm is mounted. Both arms have their power cable pointing **straight up** (see the left arm in **Figure 14**): the left arm is mounted rotated 90° about the y axis, and the right arm -90°. The cable pointing **straight down** at the base of the right arm in **Figure 14** is the **joint connector cable**, not the power cable. Do not use it to tell which way an arm is mounted.

![Mounting direction of the left and right arms](images-en/fig14-arm-direction.jpg)

# Electrical connection: power and communication

Do the electrical connection after the mechanical assembly is complete. This set of cables carries both the system power and the link to the host computer. Do all of the wiring with everything powered off, and apply power last: that is what keeps the connectors from being mixed up or plugged in wrong.

**Step 1**: connect the power cable to the power supply module to power the system.

![Power cable connected to the power supply](images-en/fig15-power.jpg)

**Step 2**: connect the XT60 output of the power supply to the controller board. If you did not order the power supply module, you can power the controller board from another supply; the connection is the same.

![The XT60 output of the power supply](images-en/fig16-power-output.jpg)

**Step 3**: connect the controller board to the port at the base of the arm.

![Controller board wiring](images-en/fig17-controller-board.jpg)

![The port at the base of the arm](images-en/fig18-arm-connector.jpg)

**Step 4**: connect the controller board to the PC with the USB cable.

## Wiring diagram

The cables and connectors correspond one-to-one with **Figure 19**.

![Overall wiring diagram](images-en/fig19-electrical-overall.jpg)

## Wiring self-check

Before you apply power, confirm each of these:

- Every connector is fully seated, with no play and no partial contact.
- Every cable goes to the right connector. Check them one by one against the labels in **Figure 19**.
- Cables are routed clear of the joints' range of motion, so that nothing is pinched or wound up while the arm moves.
- All wiring is complete and confirmed correct. Only then apply power.

# Installation notes

- Disconnect the power before you start. Do not work on a powered arm.
- Make sure every screw is tightened fully, so that nothing works loose while the arm moves.
- Check again before you apply power that every cable is connected correctly and no connector is in the wrong place.
- With the column mount, check the direction of the left and right arms (both power cables point up: the left arm is rotated 90° about the y axis and the right arm -90°; the cable pointing down at the right arm's base is the joint connector cable). An arm mounted the wrong way round will not work.
- After installation, check every fastener and cable connection before you put the arm into service.

The LITEARM-SE is now installed. Next you can install the SDK, or connect to the arm from the host software, to control it, calibrate it, and tune its motion.

SDK, host software, and documentation downloads: <https://github.com/nexform-tech>

Thank you for choosing this product. We hope it serves you well.
