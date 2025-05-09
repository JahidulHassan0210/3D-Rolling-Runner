from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18, GLUT_BITMAP_HELVETICA_12
import random
import time

# Game state
ball_x, ball_y, ball_z = 0.0, 0.5, 0.0
base_ball_speed = 0.1
ball_speed = base_ball_speed
segment_length = 10.0
num_segments = 5
segments = [i * segment_length for i in range(num_segments)]
obstacles = []
power_foods = []
ball_life = 5
game_over = False
score = 0
passed_obstacles = set()
last_time = time.time()
difficulty_level = 1
width_multiplier = 1.0

# Jump and float mechanics
is_jumping = False
jump_height = 5
jump_speed = 0.1
current_jump_height = 0.0
gravity = 0.1
is_floating = False
float_start_time = 0
float_duration = 5.0

# Camera and track settings
camera_height = 2.0
camera_distance = 5.0
track_half_width = 5.0
lane_width = 2.0
base_obstacle_size = 1.0

# Protection state
is_protected = False
protection_timer = 0
protection_duration = 5.0

# Cheat mode
cheat_mode = False
cheat_timer = 0
cheat_duration = 5.0

class Obstacle:
    def __init__(self, x, z, width_mult):
        self.x = x
        self.z = z
        self.id = random.random()
        self.has_been_passed = False
        self.width = base_obstacle_size * width_mult
        self.depth = base_obstacle_size
        self.height = base_obstacle_size

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.height / 2, self.z)
        glColor3f(0, 0, 1)
        half_w = self.width / 2
        half_h = self.height / 2
        half_d = self.depth / 2
        glBegin(GL_QUADS)
        for face in [
            [(1, 1), (-half_w, -half_h, half_d), (half_w, -half_h, half_d), (half_w, half_h, half_d), (-half_w, half_h, half_d)],
            [(0, 0), (-half_w, -half_h, -half_d), (half_w, -half_h, -half_d), (half_w, half_h, -half_d), (-half_w, half_h, -half_d)],
            [(0, 1), (-half_w, half_h, -half_d), (half_w, half_h, -half_d), (half_w, half_h, half_d), (-half_w, half_h, half_d)],
            [(1, 0), (-half_w, -half_h, -half_d), (half_w, -half_h, -half_d), (half_w, -half_h, half_d), (-half_w, -half_h, half_d)],
            [(1, 1), (-half_w, -half_h, -half_d), (-half_w, -half_h, half_d), (-half_w, half_h, half_d), (-half_w, half_h, -half_d)],
            [(0, 0), (half_w, -half_h, -half_d), (half_w, -half_h, half_d), (half_w, half_h, half_d), (half_w, half_h, -half_d)],
        ]:
            for v in face[1:]:
                glVertex3f(*v)
        glEnd()
        glPopMatrix()

class PowerFood:
    def __init__(self, x, z):
        self.x = x
        self.z = z

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, 0.3, self.z)
        glColor3f(1, 1, 0)
        glutSolidSphere(0.3, 10, 10)
        glPopMatrix()

def init():
    glClearColor(0.5, 0.7, 1.0, 1.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, 1.33, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)

def draw_ground_segment(z_pos):
    glPushMatrix()
    glTranslatef(0, 0, z_pos)
    glBegin(GL_QUADS)
    glColor3f(0.3, 0.8, 0.3)
    glVertex3f(-track_half_width, 0.0, 0.0)
    glVertex3f(track_half_width, 0.0, 0.0)
    glVertex3f(track_half_width, 0.0, -segment_length)
    glVertex3f(-track_half_width, 0.0, -segment_length)
    glEnd()
    glPopMatrix()

def draw_life_bar():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 100, 0, 100)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1, 0, 0)
    glBegin(GL_QUADS)
    glVertex2f(10, 95)
    glVertex2f(10 + 15 * ball_life, 95)
    glVertex2f(10 + 15 * ball_life, 90)
    glVertex2f(10, 90)
    glEnd()
    glColor3f(0, 0, 0)
    glRasterPos2f(70, 95)
    score_text = f"Score: {score} | Width: {width_multiplier:.1f}x"
    for ch in score_text.encode('ascii'):
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ch)

    if cheat_mode:
        glColor3f(1, 1, 0)
        glRasterPos2f(10, 85)
        for ch in b"CHEAT MODE ACTIVE":
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ch)

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_game_over():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 100, 0, 100)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor3f(1, 1, 0)
    glRasterPos2f(40, 50)
    for ch in b"Game Over":
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ch)
    glRasterPos2f(38, 45)
    final_score = f"Final Score: {score}"
    for ch in final_score.encode('ascii'):
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ch)
    glRasterPos2f(38, 40)
    final_width = f"Max Width: {width_multiplier:.1f}x"
    for ch in final_width.encode('ascii'):
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_12, ch)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    eyeX = ball_x
    eyeY = ball_y + camera_height + current_jump_height
    eyeZ = ball_z - camera_distance
    gluLookAt(eyeX, eyeY, eyeZ, ball_x, ball_y + current_jump_height, ball_z, 0, 1, 0)

    for z_pos in sorted(segments, reverse=True):
        draw_ground_segment(z_pos)

    for obs in sorted([o for o in obstacles if o.z > ball_z], key=lambda x: -x.z):
        obs.draw()

    for pf in power_foods:
        pf.draw()

    glPushMatrix()
    glTranslatef(ball_x, ball_y + current_jump_height, ball_z)
    if is_protected:
        glColor3f(0, 1, 1)
    else:
        glColor3f(1, 0, 0)
    glutSolidSphere(0.5, 20, 20)
    glPopMatrix()

    for obs in sorted([o for o in obstacles if o.z <= ball_z], key=lambda x: -x.z):
        obs.draw()

    draw_life_bar()
    if game_over:
        draw_game_over()

    glutSwapBuffers()

def check_collision():
    global ball_life, game_over
    for obs in obstacles:
        if (not is_jumping and not is_floating and
            abs(obs.z - ball_z) < obs.depth / 2 and
            abs(obs.x - ball_x) < obs.width / 2):
            if not is_protected and not cheat_mode:
                ball_life -= 1
                if ball_life <= 0:
                    game_over = True
            obstacles.remove(obs)
    for pf in power_foods[:]:
        if abs(pf.z - ball_z) < 0.5 and abs(pf.x - ball_x) < 0.5:
            activate_protection()
            power_foods.remove(pf)

def activate_protection():
    global is_protected, protection_timer
    is_protected = True
    protection_timer = time.time()

def update_score_and_difficulty():
    global score, passed_obstacles, ball_speed, difficulty_level, width_multiplier
    for obs in obstacles:
        if ball_z > obs.z + obs.depth / 2 and not obs.has_been_passed:
            score_gain = 10 if not cheat_mode else 20
            score += score_gain
            obs.has_been_passed = True
            passed_obstacles.add(obs.id)
            difficulty_level += 1
            width_multiplier = min(4.0, width_multiplier * 1.15)
            speed_factor = 0.03 if not cheat_mode else 0.05
            ball_speed = base_ball_speed * (1 + difficulty_level * speed_factor)

def update_jump():
    global is_jumping, current_jump_height, is_floating
    if is_floating:
        if time.time() - float_start_time >= float_duration:
            is_floating = False
    elif is_jumping:
        current_jump_height += jump_speed
        if current_jump_height >= jump_height:
            is_jumping = False
    else:
        if current_jump_height > 0:
            current_jump_height -= gravity
            if current_jump_height < 0:
                current_jump_height = 0

def update_protection():
    global is_protected
    if is_protected and (time.time() - protection_timer > protection_duration):
        is_protected = False

def update_cheat_mode():
    global cheat_mode
    if cheat_mode and (time.time() - cheat_timer > cheat_duration):
        cheat_mode = False

def idle():
    global ball_z, segments, obstacles, power_foods, last_time
    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time

    if not game_over:
        ball_z += ball_speed * delta_time * 60
        update_jump()
        update_protection()
        update_cheat_mode()
        check_collision()
        update_score_and_difficulty()

        if ball_z > segments[0] + segment_length:
            segments.pop(0)
            new_z = segments[-1] + segment_length
            segments.append(new_z)
            lane = random.choice([-2.0, 0.0, 2.0])
            obstacles.append(Obstacle(lane, new_z - segment_length / 2, width_multiplier))
            if random.random() < 0.3:
                power_lane = random.choice([-2.0, 0.0, 2.0])
                power_foods.append(PowerFood(power_lane, new_z - segment_length * 0.75))

        obstacles = [obs for obs in obstacles if obs.z > ball_z - 5.0]
        power_foods = [pf for pf in power_foods if pf.z > ball_z - 5.0]

    glutPostRedisplay()

def on_special_key(key, x, y):
    global ball_x, is_jumping, current_jump_height
    if game_over:
        return
    if key == GLUT_KEY_RIGHT and ball_x - lane_width >= -track_half_width:
        ball_x -= lane_width
    elif key == GLUT_KEY_LEFT and ball_x + lane_width <= track_half_width:
        ball_x += lane_width
    elif key == GLUT_KEY_UP and not is_jumping and not is_floating and current_jump_height == 0:
        is_jumping = True

def on_keyboard(key, x, y):
    global is_jumping, current_jump_height, game_over, ball_x, ball_y, ball_z
    global obstacles, power_foods, ball_life, score, passed_obstacles
    global difficulty_level, ball_speed, width_multiplier
    global cheat_mode, cheat_timer, is_floating, float_start_time

    if key == b' ' and not is_floating and current_jump_height == 0:
        is_floating = True
        float_start_time = time.time()
        current_jump_height = jump_height
    elif key == b'r' or key == b'R':
        ball_x, ball_y, ball_z = 0.0, 0.5, 0.0
        ball_speed = base_ball_speed
        segments[:] = [i * segment_length for i in range(num_segments)]
        obstacles.clear()
        power_foods.clear()
        ball_life = 5
        score = 0
        passed_obstacles.clear()
        width_multiplier = 1.0
        difficulty_level = 1
        is_protected = False
        current_jump_height = 0.0
        is_jumping = False
        is_floating = False
        cheat_mode = False
        global game_over
        game_over = False
    elif key == b'c' or key == b'C':
        cheat_mode = True
        cheat_timer = time.time()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"Jumping Ball with Floating Mechanic")
    init()
    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutSpecialFunc(on_special_key)
    glutKeyboardFunc(on_keyboard)
    glutMainLoop()

if __name__ == "__main__":
    main()