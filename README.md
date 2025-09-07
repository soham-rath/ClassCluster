# ClassCluster

**ClassCluster** is a smart classroom seating optimizer built in Python. It automatically arranges students based on friendships, conflicts, skill levels, and seating preferences, helping teachers create a harmonious and productive classroom environment.

---

## Features

- Automatic seating based on:
  - Friendships and conflicts
  - Proximity to teacher
  - Skill levels
  - Front/back seating preferences
  - Optional adjacency requirements
- Interactive **drag-and-drop** GUI to move students around
- Click a student to **edit information inline**
- Real-time **score evaluation** and **flashing indicators** for conflicts/bonuses
- **Undo/Redo** functionality
- CSV import/export for saving/loading seating arrangements
- Clustering logic to keep students together when there are few students

---

## Built With

- **Python** – main programming language  
- **Tkinter** – GUI framework  
- **CSV** – for saving/loading seating arrangements  
- **Random** – for randomized placement in the algorithm  
- **Copy (deepcopy)** – for undo/redo functionality  

---

## Installation

1. Clone the repository:
```bash
git clone https://github.com/soham-rath/ClassCluster.git
cd ClassCluster
```

2. Make sure Python 3 is installed.

3. Run the app:
```bash
python main.py
```

---

## Usage

- Click on a student to edit their name, skill, friends, conflicts, or seating preferences.  
- Long-press and drag a student to move them to a new seat.  
- Use **Undo/Redo** buttons or `Ctrl+Z / Ctrl+Y` to revert changes.  
- Use **Export CSV** and **Import CSV** to save/load classroom arrangements.  
- Click **Re-optimize** to automatically rearrange students for the best score.  

---

## Scoring Logic

The seating score \(S\) is calculated as:

$$
S = 10 + \sum_{\text{students}} \Big( B_\text{friends} - P_\text{avoid} + T_\text{teacher} - F_\text{front/back} \Big)
$$

Where:  
- $$B_\text{friends}\$$ = bonus for being next to friends  
- $$P_\text{avoid}\$$ = penalty for sitting next to students to avoid  
- $$T_\text{teacher}\$$ = adjustment for proximity to teacher  
- $$F_\text{front/back}\$$ = penalty if front/back preferences are not respected  

Score is clamped between 1 and 10 for visualization.

---

## Challenges

- Making drag-and-drop intuitive while keeping click-to-edit functional  
- Balancing multiple constraints for scoring  
- Implementing inline editing for any number of students  
- Ensuring students cluster naturally instead of spreading across the classroom  

---

## Future Improvements

- Enhance clustering to always seat friends next to each other  
- Support multiple classroom layouts  
- Include additional constraints like group projects or accessibility needs  
- Create a web version with cloud saving and sharing  

---
