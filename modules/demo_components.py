"""Shared dispatch for browser widgets, local CLI and trusted bot intents."""
from . import demo_trading as demo

KINDS=('demo-account','demo-trade','demo-bot','demo-positions','demo-reports')


def run(kind,data):
    data=dict(data);owner=data.pop('_state_owner',None);slot=data.pop('_state_slot',None)
    demo.owner_key(owner)
    action=data.pop('action','submit' if kind=='demo-bot' and any(key in data for key in ('price','entry','ACTION','tradePIN','trade_pin')) else 'state')
    # ACTION is the public trade direction; lowercase action is the component
    # operation. When action is BUY/SELL, interpret it as a bot order intent.
    if kind=='demo-bot' and action in ('buy','sell','BUY','SELL'):
        data['ACTION']=action;action='submit'
    if action in ('state','get'):
        if set(data)-{'account_id'}:raise ValueError('Invalid demo state input')
        if kind=='demo-reports':return demo.report(owner,data.get('account_id'))
        return demo.state(owner,data.get('account_id'),slot if kind in ('demo-trade','demo-bot') else None)
    if kind=='demo-account':
        if action=='create':
            if set(data)-{'name','initial_balance','tradePIN','settings'}:raise ValueError('Invalid account input')
            return {'account':demo.create_account(owner,data.get('name'),data.get('initial_balance'),data.get('tradePIN'),data.get('settings'))}
        if action=='select' and set(data)=={'account_id'}:return {'account':demo.select_account(owner,data['account_id'])}
        if action=='settings' and set(data)=={'account_id','settings'}:return {'account':demo.update_settings(owner,data['account_id'],data['settings'])}
    if kind=='demo-trade' and action=='open':return demo.submit(owner,data,'manual',slot)
    if kind=='demo-bot' and action=='submit':return demo.submit(owner,data,'bot',slot)
    if kind in ('demo-trade','demo-bot','demo-positions') and action in ('close','cancel','chart'):
        if set(data)-{'trade_id','show_on_chart'}:raise ValueError('Invalid trade action')
        return {'trade':demo.alter_order(owner,data.get('trade_id'),action,data.get('show_on_chart'))}
    if kind=='demo-reports' and action=='report':
        if set(data)-{'account_id','since','until'}:raise ValueError('Invalid report input')
        return demo.report(owner,**data)
    raise ValueError('Unknown demo component action')
