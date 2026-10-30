"""Owner-scoped reusable indicator configurations."""
from uuid import uuid4
from market_data import indicators
from .module_state import change

DEFAULTS = [
    {'id':'sma-default', 'name':'SMA 20', 'type':'sma', 'parameters':{'period':20}, 'enabled':True},
    {'id':'rsi-default', 'name':'RSI 14', 'type':'rsi', 'parameters':{'period':14}, 'enabled':False},
    {'id':'macd-default', 'name':'MACD 12/26/9', 'type':'macd', 'parameters':{'fast':12, 'slow':26, 'signal':9}, 'enabled':False},
]


def list_profiles(owner):
    return change(owner, 'indicator-profiles', 'catalog', DEFAULTS, lambda old: (old, False))


def save(owner, data, profile_id=None):
    if not isinstance(data, dict) or set(data) != {'name', 'type', 'parameters', 'enabled'}:
        raise ValueError('invalid indicator configuration')
    name, kind, enabled = data['name'], data['type'], data['enabled']
    if not isinstance(name, str) or not name.strip() or len(name) > 80 or type(enabled) is not bool:
        raise ValueError('invalid indicator name or status')
    if not isinstance(kind, str): raise ValueError('invalid indicator type')
    parameters = indicators.normalize(kind, data['parameters'])
    ident = profile_id or 'ind-' + uuid4().hex[:12]
    profile = {'id':ident, 'name':name.strip(), 'type':kind, 'parameters':parameters, 'enabled':enabled}
    def update(old):
        existing = next((index for index, item in enumerate(old) if item['id'] == ident), None)
        if profile_id is not None and existing is None: raise LookupError('indicator not found')
        if existing is None:
            if len(old) >= 24: raise ValueError('indicator limit reached')
            old = [*old, profile]
        else:
            old = list(old); old[existing] = profile
        return old, True
    change(owner, 'indicator-profiles', 'catalog', DEFAULTS, update)
    return profile


def delete(owner, profile_id):
    def update(old):
        new = [item for item in old if item['id'] != profile_id]
        if len(new) == len(old): raise LookupError('indicator not found')
        return new, True
    change(owner, 'indicator-profiles', 'catalog', DEFAULTS, update)
