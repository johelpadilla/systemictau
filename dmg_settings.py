# dmgbuild settings for Systemic Tau
# Can be overridden with -D on command line
import os

# Get defines
files = defines.get('files', ['dist/SystemicTau.app'])
app_name = os.path.basename(files[0]).replace('.app', '')

format = 'UDBZ'
size = None
files = files
symlinks = { 'Applications': '/Applications' }

icon = defines.get('icon', '')
if icon and os.path.exists(icon):
    badge_icon = icon
else:
    badge_icon = None

icon_locations = {
    os.path.basename(files[0]): (140, 120),
    'Applications': (500, 120)
}

background = 'builtin-arrow'
show_status_bar = False
show_tab_view = False
show_toolbar = False
show_pathbar = False
show_sidebar = False
window_rect = ((100, 100), (640, 280))

# Volume name will be passed as argument to dmgbuild
volume_name = defines.get('volume_name', 'Systemic Tau')