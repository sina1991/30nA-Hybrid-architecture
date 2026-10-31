"""Session Windows Pro Inputs supplied by the user, without executing EX5.

Times are preserved literally as broker wall times. The EX5-only Supported
broker detection and its hidden reference-time conversion are not assumed.
"""

def mt5_color(value):
    """MQL color integers store bytes as 0x00BBGGRR, not RGB."""
    return '#%02x%02x%02x' % (value & 255, (value >> 8) & 255, (value >> 16) & 255)


WINDOW_INPUTS = (
    ('01:00','02:30',6903890,3),('02:30','03:00',12497408,1),
    ('03:00','07:00',6584372,2),('07:00','10:00',3437696,2),
    ('10:00','13:00',2929407,1),('13:00','15:30',4872290,3),
    ('15:30','16:30',3960556,1),('16:30','18:00',6309620,1),
    ('18:00','21:00',14714442,2),('21:00','23:00',13656182,2),
    ('23:00','00:00',8143456,3),
)
TIME_POINTS = '02:30,03:00,04:00,07:00,08:00,09:00,10:00,13:00,15:30,16:30,17:00,18:00,20:00,21:00,23:00'
PRESET = {
    'winter_utc_minutes':120,'clock_change':'Europe','reference_timezone':None,
    'schedule_shift_minutes':0,'teaching_view':'Full map','days':10,
    'windows':[{'name':'Window %02d' % (index+1),'start':start,'end':end,'color':mt5_color(col),'grade':{1:'A',2:'B',3:'C'}[grade],'views':[]} for index,(start,end,col,grade) in enumerate(WINDOW_INPUTS)],
    'points':[{'time':point,'views':[]} for point in TIME_POINTS.split(',')],
    'clock_size':360,'position':{'x':1.0,'y':1.0},'points_on_clock':True,'show_seconds':True,'highlight_minutes':5,
    'point_color':mt5_color(7260392),'label_color':mt5_color(12169130),
    'label_size':9,'label_font':'Segoe UI','stagger_labels':True,'grade_in_label':True,
    'point_style':'dotted','point_width':1,'point_labels':True,
    'day_line_color':mt5_color(8022372),'day_line_style':'dashed','day_line_width':1,'day_line_label':True,
    'border_width':1,'grade_opacity':{'A':0.28,'B':0.16,'C':0.08},
    'panel_position':{'x':1.0,'y':0.0},'panel_font_size':10,'panel_font':'Segoe UI',
}
