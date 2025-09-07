import tkinter as tk
from tkinter import messagebox, filedialog
from copy import deepcopy
import csv, random
import time

# ------------------------------
# 1. Student Class
# ------------------------------
class Student:
    def __init__(self, name, skill=1, avatar=None,
                 avoid=None, friends=None,
                 must_front=False, must_back=False,
                 must_next_to=None,
                 near_teacher=False, far_teacher=False):
        self.name = name
        self.skill = skill
        self.avatar = avatar if avatar else name[0].upper()
        self.avoid = set(avoid) if avoid else set()
        self.friends = set(friends) if friends else set()
        self.must_front = must_front
        self.must_back = must_back
        self.must_next_to = set(must_next_to) if must_next_to else set()
        self.near_teacher = near_teacher
        self.far_teacher = far_teacher

# ------------------------------
# 2. Classroom Config
# ------------------------------
ROWS = 4
COLS = 5
TEACHER_POS = [(0, 2)]

def empty_seating():
    return [[None for _ in range(COLS)] for _ in range(ROWS)]

def neighbors(r,c):
    return [(r+dr,c+dc) for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]
            if 0<=r+dr<ROWS and 0<=c+dc<COLS]

# ------------------------------
# 3. Scoring
# ------------------------------
def score_seating(seating):
    score = 10
    for r in range(ROWS):
        for c in range(COLS):
            s = seating[r][c]
            if not s: continue
            for nr,nc in neighbors(r,c):
                n = seating[nr][nc]
                if n:
                    if n.name in s.avoid: score -= 1
                    if n.name in s.friends: score += 0.5
                    if n.name in s.must_next_to and n.name in s.must_next_to: score += 1
            for tr,tc in TEACHER_POS:
                dist = abs(tr-r)+abs(tc-c)
                if s.near_teacher: score += 1/(dist+1)
                if s.far_teacher: score -= 1/(dist+1)
            if s.must_front and r != 0: score -= 1
            if s.must_back and r != ROWS-1: score -=1
    return max(1, min(score, 10))

# ------------------------------
# 4. Greedy Clustered Placement
# ------------------------------
def greedy_place_students(seating, students):
    seats = [(r,c) for r in range(ROWS) for c in range(COLS) if (r,c) not in TEACHER_POS]
    random.shuffle(seats)
    placed = set()
    for student in students:
        best_score = -float('inf')
        best_pos = None
        target_seats = seats.copy()
        if placed:
            neighbors_seats = []
            for r0,c0 in placed:
                for nr,nc in neighbors(r0,c0):
                    if seating[nr][nc] is None and (nr,nc) not in TEACHER_POS:
                        neighbors_seats.append((nr,nc))
            if neighbors_seats:
                target_seats = neighbors_seats
        for r,c in target_seats:
            if seating[r][c] is None:
                seating[r][c] = student
                s = score_seating(seating)
                if s > best_score:
                    best_score = s
                    best_pos = (r,c)
                seating[r][c] = None
        if best_pos:
            seating[best_pos[0]][best_pos[1]] = student
            placed.add(best_pos)
    return seating

# ------------------------------
# 5. GUI
# ------------------------------
class SeatingApp:
    def __init__(self, seating, students):
        self.root = tk.Tk()
        self.root.title("ClassCluster")
        self.students = students
        self.seating = seating
        self.undo_stack = []
        self.redo_stack = []
        self.dragged_student = None
        self.drag_start = None
        self.flash_state = False
        self.edit_panel = None
        self.edit_entries = {}
        self.drag_start_time = None

        self.create_widgets()
        self.update_grid()
        self.animate_flashing()
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        self.root.mainloop()

    def create_widgets(self):
        self.frame_grid = tk.Frame(self.root)
        self.frame_grid.pack(side=tk.LEFT)
        self.buttons = [[None for _ in range(COLS)] for _ in range(ROWS)]
        for r in range(ROWS):
            for c in range(COLS):
                btn = tk.Button(self.frame_grid, text="", width=12, height=3)
                btn.grid(row=r, column=c)
                btn.bind("<ButtonPress-1>", lambda e,row=r,col=c:self.start_drag(row,col))
                btn.bind("<ButtonRelease-1>", lambda e,row=r,col=c:self.drop_student(row,col))
                btn.bind("<Enter>", lambda e,row=r,col=c:self.show_tooltip(row,col))
                btn.bind("<Leave>", lambda e:self.hide_tooltip())
                btn.bind("<Double-Button-1>", lambda e,row=r,col=c:self.edit_student)
                self.buttons[r][c] = btn

        self.frame_ctrl = tk.Frame(self.root)
        self.frame_ctrl.pack(side=tk.RIGHT, fill=tk.Y)
        tk.Button(self.frame_ctrl, text="Undo", command=self.undo).pack(pady=2)
        tk.Button(self.frame_ctrl, text="Redo", command=self.redo).pack(pady=2)
        tk.Button(self.frame_ctrl, text="Reset", command=self.reset_seating).pack(pady=2)
        tk.Button(self.frame_ctrl, text="Re-optimize", command=self.reoptimize).pack(pady=2)
        tk.Button(self.frame_ctrl, text="Export CSV", command=self.export_csv).pack(pady=2)
        tk.Button(self.frame_ctrl, text="Import CSV", command=self.import_csv).pack(pady=2)
        self.score_label = tk.Label(self.frame_ctrl, text=f"Score: {score_seating(self.seating):.2f}")
        self.score_label.pack(pady=5)

        self.tooltip = tk.Label(self.root, text="", bg="yellow")
        self.tooltip.place_forget()

    # -------------------------
    # Drag & Drop
    # -------------------------
    def start_drag(self,r,c):
        if (r,c) in TEACHER_POS: return
        self.dragged_student = self.seating[r][c]
        self.drag_start = (r,c)
        self.drag_start_time = time.time()
        self.buttons[r][c].config(relief=tk.SUNKEN)

    def drop_student(self,r,c):
        if not self.dragged_student: return
        if time.time() - self.drag_start_time < 0.2:
            # consider it a click -> edit
            self.edit_student(r,c)
        else:
            # consider it a drag
            if (r,c) in TEACHER_POS:
                messagebox.showwarning("Invalid Move", "Cannot place student on teacher desk!")
                self.buttons[self.drag_start[0]][self.drag_start[1]].config(relief=tk.RAISED)
            else:
                self.save_undo()
                self.seating[self.drag_start[0]][self.drag_start[1]], self.seating[r][c] = self.seating[r][c], self.dragged_student
        self.dragged_student = None
        self.drag_start = None
        self.drag_start_time = None
        self.update_grid()

    # -------------------------
    # Undo/Redo
    # -------------------------
    def save_undo(self):
        self.undo_stack.append(deepcopy(self.seating))
        if len(self.undo_stack)>50: self.undo_stack.pop(0)

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(deepcopy(self.seating))
            self.seating=self.undo_stack.pop()
            self.update_grid()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(deepcopy(self.seating))
            self.seating=self.redo_stack.pop()
            self.update_grid()

    # -------------------------
    # Reset / Re-optimize
    # -------------------------
    def reset_seating(self):
        self.save_undo()
        self.seating = empty_seating()
        self.update_grid()

    def reoptimize(self):
        self.save_undo()
        self.seating = greedy_place_students(empty_seating(), self.students)
        self.update_grid()

    # -------------------------
    # Update Grid
    # -------------------------
    def get_color(self,r,c):
        s = self.seating[r][c]
        if not s: return "white"
        penalty=0
        bonus=0
        for nr,nc in neighbors(r,c):
            n = self.seating[nr][nc]
            if n:
                if n.name in s.avoid: penalty+=1
                if n.name in s.friends: bonus+=1
                if n.name in s.must_next_to and n.name not in s.must_next_to: penalty+=1
        if penalty>0: return "red" if not self.flash_state else "darkred"
        if bonus>0: return "lightgreen" if not self.flash_state else "green"
        return "white"

    def update_grid(self):
        for r in range(ROWS):
            for c in range(COLS):
                btn=self.buttons[r][c]
                s = self.seating[r][c]
                text = "T" if (r,c) in TEACHER_POS else (s.name if s else "")
                color=self.get_color(r,c) if (r,c) not in TEACHER_POS else "lightblue"
                btn.config(text=text,bg=color,relief=tk.RAISED)
        self.score_label.config(text=f"Score: {score_seating(self.seating):.2f}")

    # -------------------------
    # Tooltip
    # -------------------------
    def show_tooltip(self,r,c):
        s = self.seating[r][c]
        if not s: return
        info=f"{s.name}\nSkill:{s.skill}\nAvoid:{','.join(s.avoid)}\nFriends:{','.join(s.friends)}\nFront:{s.must_front} Back:{s.must_back}\nNextTo:{','.join(s.must_next_to)}\nNearT:{s.near_teacher} FarT:{s.far_teacher}"
        self.tooltip.config(text=info)
        self.tooltip.place(x=self.root.winfo_pointerx()-self.root.winfo_rootx()+10,
                           y=self.root.winfo_pointery()-self.root.winfo_rooty()+10)
    def hide_tooltip(self):
        self.tooltip.place_forget()

    # -------------------------
    # Flashing animation
    # -------------------------
    def animate_flashing(self):
        self.flash_state = not self.flash_state
        self.update_grid()
        self.root.after(500, self.animate_flashing)

    # -------------------------
    # CSV Import/Export
    # -------------------------
    def export_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if not path: return
        with open(path,"w",newline="") as f:
            writer = csv.writer(f)
            for r in range(ROWS):
                row=[]
                for c in range(COLS):
                    s=self.seating[r][c]
                    if s:
                        row.append(f"{s.name}|{s.skill}|{','.join(s.avoid)}|{','.join(s.friends)}|{s.must_front}|{s.must_back}|{','.join(s.must_next_to)}|{s.near_teacher}|{s.far_teacher}|{s.avatar}")
                    else: row.append("")
                writer.writerow(row)
        messagebox.showinfo("Export","CSV saved.")

    def import_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV","*.csv")])
        if not path: return
        new_seating = empty_seating()
        with open(path,"r") as f:
            reader = csv.reader(f)
            for r,row in enumerate(reader):
                for c,cell in enumerate(row):
                    if cell.strip():
                        parts = cell.split("|")
                        s=Student(parts[0],int(parts[1]),avatar=parts[9],
                                  avoid=parts[2].split(",") if parts[2] else [],
                                  friends=parts[3].split(",") if parts[3] else [],
                                  must_front=parts[4]=="True",
                                  must_back=parts[5]=="True",
                                  must_next_to=parts[6].split(",") if parts[6] else [],
                                  near_teacher=parts[7]=="True",
                                  far_teacher=parts[8]=="True")
                        new_seating[r][c]=s
        self.seating=new_seating
        self.update_grid()

    # -------------------------
    # Edit Student
    # -------------------------
    def edit_student(self,r,c):
        student = self.seating[r][c]
        if not student: return
        if self.edit_panel and self.edit_panel.winfo_exists():
            self.edit_panel.destroy()
        self.edit_panel = tk.Frame(self.root, bd=2, relief=tk.RIDGE)
        self.edit_panel.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        fields = ["Name","Skill","Avatar","Avoid","Friends","MustFront","MustBack","MustNextTo","NearTeacher","FarTeacher"]
        vals=[student.name,student.skill,student.avatar,
              ",".join(student.avoid),",".join(student.friends),
              student.must_front,student.must_back,
              ",".join(student.must_next_to),
              student.near_teacher,student.far_teacher]
        self.edit_entries={}
        for i,f in enumerate(fields):
            tk.Label(self.edit_panel,text=f).grid(row=i,column=0)
            e=tk.Entry(self.edit_panel)
            e.grid(row=i,column=1)
            e.insert(0,str(vals[i]))
            self.edit_entries[f]=e

        def save_student(event=None):
            student.name = self.edit_entries["Name"].get()
            try: student.skill=int(self.edit_entries["Skill"].get())
            except: student.skill=1
            student.avatar = self.edit_entries["Avatar"].get()
            student.avoid = set(self.edit_entries["Avoid"].get().split(",")) if self.edit_entries["Avoid"].get() else set()
            student.friends = set(self.edit_entries["Friends"].get().split(",")) if self.edit_entries["Friends"].get() else set()
            student.must_front = self.edit_entries["MustFront"].get()=="True"
            student.must_back = self.edit_entries["MustBack"].get()=="True"
            student.must_next_to = set(self.edit_entries["MustNextTo"].get().split(",")) if self.edit_entries["MustNextTo"].get() else set()
            student.near_teacher = self.edit_entries["NearTeacher"].get()=="True"
            student.far_teacher = self.edit_entries["FarTeacher"].get()=="True"
            self.update_grid()
            if self.edit_panel and self.edit_panel.winfo_exists():
                self.edit_panel.destroy()

        tk.Button(self.edit_panel,text="Save",command=save_student).grid(row=len(fields),column=0,columnspan=2)
        self.edit_panel.bind_all("<Return>", save_student)

# ------------------------------
# 6. Demo Students
# ------------------------------
students = [
    Student("Alice",skill=5,friends={"Bob"},avoid={"Eve"},must_back=True),
    Student("Bob",skill=3,friends={"Alice"},avoid=set(),must_front=True),
    Student("Charlie",skill=2,friends={"Eve"},avoid=set(),near_teacher=True),
    Student("David",skill=4,friends=set(),avoid={"Alice"},far_teacher=True),
    Student("Eve",skill=1,friends={"Charlie"},avoid={"Bob"}),
    Student("Frank",skill=2),
]

seating = greedy_place_students(empty_seating(), students)
app = SeatingApp(seating, students)
