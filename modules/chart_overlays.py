"""Owner-scoped technical indicator profiles projected onto the price chart."""
import time
from . import technical


def calculate(owner, profiles, chart, end_time=None):
    overlays=[]
    for profile in profiles:
        if profile['type'] not in technical.KINDS or not profile['enabled']: continue
        config=profile['parameters']
        data={'settings':config,'_state_owner':owner,'_state_slot':profile['id']}
        if profile['type']=='round-levels':
            # The automatic step is based on current market price, independent
            # of historical panning. Visible line placement happens in the SVG.
            candles=chart.get('candles',[])
            if candles:
                data.update(visible_low=min(row['low'] for row in candles),visible_high=max(row['high'] for row in candles))
        else:
            data['now']=end_time if end_time is not None else time.time()
            if profile['type'] in ('session-clock','session-windows'):
                data['settings']={**config,'chart_minutes':int(chart['interval'][:-1])}
        try:
            if profile['type'] in ('session-clock','session-windows'):
                cfg=technical.settings(profile['type'],data['settings'])
                result=technical.clock_result(cfg,time.time())
                if cfg['winter_utc_minutes'] is not None and (profile['type']=='session-windows' or cfg['chart_point_lines']):
                    result.update(technical.session_chart(cfg,{},end_time if end_time is not None else time.time()))
            else:
                result=technical.run(profile['type'],data)
            result.pop('candles',None)
        except (OSError,ValueError,TypeError,KeyError):
            result={'status':'unavailable','message':'Indicator data unavailable','settings':config}
        overlays.append({**profile,'result':result})
    return overlays
