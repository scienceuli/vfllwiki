# Tmux

### tmux - The "Perpetual Motion Machine" in Your Terminal

After covering SSH, let’s talk about its great partner, tmux. Its full name is Terminal Multiplexer. Sounds fancy, but it simply means: you can run multiple terminals in one terminal window, and even if your SSH connection drops, your running commands won’t stop.

Imagine this scenario: You’re running a 3-hour data sync on a server, and your home router reboots, killing the SSH connection. Without tmux, the task fails and you have to start over. With tmux, the task keeps running in the background. You reconnect, attach to it, and everything is as it was.

**Core Concepts of tmux**

tmux has three layers. Once you understand them, it’s easy:

- **Session**: The largest unit, like a workspace. You can have multiple sessions, each running independently.
- **Window**: Tabs within a session, similar to browser tabs.
- **Pane**: Split screens within a window. A window can be divided into multiple panes horizontally or vertically.

**Common Commands**

- **Create a session:**
```
tmux new -s mywork
```
- **List all sessions:**
```
tmux ls
```
- **Reattach to a session:**
```
tmux attach -t mywork
```
- **Detach from the current session (without terminating it):**
```
Press `Ctrl+b`, then `d` (for detach).
```
- **Kill a session:**
```
tmux kill-session -t mywork
```
Press enter or click to view image in full size

![](https://miro.medium.com/v2/resize:fit:1400/1*1TzHBc2mctI-me2TrcGBxA.png)

**Window and Pane Operations**

All tmux operations start with the prefix `Ctrl+b`. Press `Ctrl+b`, release it, then press another key:

**Window operations:**

- `Ctrl+b + c`: Create a new window
- `Ctrl+b + n`: Next window
- `Ctrl+b + p`: Previous window
- `Ctrl+b + number`: Jump to the Nth window
- `Ctrl+b + w`: List all windows, navigate with arrow keys

**Pane operations (splitting):**

- `Ctrl+b + %`: Split vertically (left-right)
- `Ctrl+b + "`: Split horizontally (top-bottom)
- `Ctrl+b + arrow keys`: Switch between panes
- `Ctrl+b + z`: Full-screen current pane; press again to restore
- `Ctrl+b + x`: Close the current pane

**tmux Configuration File**

The default tmux prefix key `Ctrl+b` can feel awkward to use. I recommend changing it to `Ctrl+a` to match screen. Create `~/.tmux.conf`:
```
# Change prefix key to Ctrl+a  
set -g prefix C-a  
unbind C-b  
bind C-a send-prefix  
  
# Enable mouse support  
set -g mouse on  
  
# Start window numbering from 1  
set -g base-index 1  
  
# 256-color support  
set -g default-terminal "screen-256color"  
  
# Increase history limit to 50000 lines  
set -g history-limit 50000

After modifying the configuration, execute `Ctrl+b` then `:source-file ~/.tmux.conf` in tmux to hot-reload.
```
### Practical SSH + tmux Collaboration

Combining SSH and tmux is the true "ultimate remote Ops solution."

**▸ Scenario 1: Running Long Tasks Without Fear of Disconnection**

This is the most common use case. Connect to the server, start tmux:
```
ssh user@server  
tmux new -s backup
```
- Run your long task inside tmux
- Then `Ctrl+b`, `d` to detach
- Even if SSH disconnects, the task continues

Next time you reconnect: `ssh user@server`, then `tmux attach -t backup`, everything resumes as before.

**▸ Scenario 2: Multiple Users Collaborating in the Same tmux Session**

tmux supports multiple users connecting to the same session simultaneously, like a "pair programming" terminal version:

- A creates a session:
```
tmux new -s pair
```
- B connects to the same session:
```
tmux attach -t pair
```
Both see the exact same terminal interface; any commands entered by one are visible in real-time to the other. Great for remote troubleshooting.

**▸ Scenario 3: Auto-Enter tmux on SSH Connection**

If you want to automatically enter tmux (create if none exists, resume if there is) every time you SSH in, add this to the server's `~/.bashrc`:
```
# If SSH login and not in tmux, auto-attach or create  
if [ -n "$SSH_CONNECTION" ] && [ -z "$TMUX" ]; then  
    tmux attach -t default 2>/dev/null || tmux new -s default  
fi
```
Now, every SSH login automatically enters a tmux session named "default". Disconnect and reconnect, and you're back to the original state. Once you try it, you'll never go back.

### Advanced SSH Tips

- **One-Click Access via Jump Host:**

Need to access an internal machine through a jump host? No need for manual two-step; configure ProxyJump for a one-step solution:
```
Host inner-server  
    HostName 10.0.0.50  
    User admin  
    ProxyJump jump-host
```
Directly `ssh inner-server`, automatically jumping through jump-host.

- **SSH Connection Multiplexing:**

Tired of re-handshaking every time you connect to the same server repeatedly? Use Connection Multiplexing to speed it up:
```
Host *  
    ControlMaster auto  
    ControlPath ~/.ssh/control-%r@%h:%p  
    ControlPersist 600
```
The first connection establishes a master channel; subsequent connections reuse it for lightning-fast speed.

- **SCP File Transfer:**
- **Upload:**
```
scp local_file user@remote:/path/
```
- **Download:**
```
scp user@remote:/path/file
```
- **Recursive Copy:**
```
scp -r local_dir user@remote:/path/
```
