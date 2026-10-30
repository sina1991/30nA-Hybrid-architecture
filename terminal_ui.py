"""Numbered interactive workspace over the same 30na CLI used in scripts."""
import json
import math
import os
from pathlib import Path
import subprocess
import sys


class Terminal:
    def __init__(self, owner='customer', manager_url='https://localhost:18444',
                 token_file='/etc/30na/customer-token', ca_file='/etc/30na/ca/trust.pem'):
        self.owner, self.manager_url = owner, manager_url
        self.token_file, self.ca_file = token_file, ca_file
        self.program = str(Path(__file__).resolve().parent / '30na')
        self.slot_rows, self.module_rows, self.worker_rows = None, None, None
        self.health = None

    def ask(self, label, default=None):
        suffix = f' [{default}]' if default is not None else ''
        value = input(label + suffix + ': ').strip()
        return value if value else (str(default) if default is not None else '')

    def choose(self, title, rows, label, default=0):
        if not rows:
            print('No items available.')
            return None
        print('\n' + title)
        for index, row in enumerate(rows, 1):
            print(f'  {index}. {label(row)}')
        print('  0. Back')
        while True:
            value = self.ask('Select a number', str(default))
            if value == '0': return None
            if value.isascii() and value.isdigit() and 1 <= int(value) <= len(rows):
                return rows[int(value) - 1]
            print('Enter a number from the list.')

    def call(self, args, *, state=False, quiet=False):
        command = [sys.executable, self.program, *args]
        if state and os.geteuid() == 0:
            command = ['runuser', '-u', '30na', '--', *command]
        try:
            completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        except OSError:
            if not quiet: print('Could not start the command.', file=sys.stderr)
            return None
        if completed.returncode:
            if not quiet:
                print(completed.stderr.rstrip() or 'Operation failed.', file=sys.stderr)
            return None
        if completed.stderr and not quiet:
            print(completed.stderr.rstrip(), file=sys.stderr)
        try:
            return json.loads(completed.stdout)
        except ValueError:
            if not quiet: print('Invalid response from command.', file=sys.stderr)
            return None

    def show(self, value):
        if value is not None:
            print(json.dumps(value, ensure_ascii=False, indent=2))

    def slot_args(self, *args):
        return ['slots', '--owner', self.owner, *args]

    def worker_args(self, *args):
        return ['workers', '--manager-url', self.manager_url, '--token-file', self.token_file,
                '--ca-file', self.ca_file, *args]

    def refresh(self):
        print('\nLoading status...')
        slots = self.call(self.slot_args('list'), state=True, quiet=True)
        modules = self.call(['modules', 'list'], quiet=True)
        workers = self.call(self.worker_args('list'), quiet=True)
        health = self.call(['modules', 'run', 'dashboard-health'], quiet=True)
        self.slot_rows = slots.get('slots', []) if isinstance(slots, dict) else None
        self.module_rows = modules.get('modules', []) if isinstance(modules, dict) else None
        self.worker_rows = workers.get('workers', []) if isinstance(workers, dict) else None
        self.health = health.get('status', 'unknown') if isinstance(health, dict) else 'unavailable'

    def overview(self):
        def count(value): return str(len(value)) if value is not None else 'unavailable'
        enabled = sum(row.get('lifecycle') == 'enabled' for row in (self.worker_rows or []))
        print('\n' + '=' * 48)
        print('30nA  |  Owner: ' + self.owner)
        print(f'Dashboard: {self.health}  |  Slots: {count(self.slot_rows)}  |  Modules: {count(self.module_rows)}')
        print(f'Workers: {count(self.worker_rows)}' + (f' ({enabled} enabled)' if self.worker_rows is not None else ''))
        print('=' * 48)
        print('  1. Slots')
        print('  2. Modules')
        print('  3. Workers and executions')
        print('  4. Refresh status')
        print('  5. Account and connection settings')
        print('  0. Exit')

    def input_for(self, module_id):
        if module_id == 'calculator':
            a = self.number('First number', 0)
            b = self.number('Second number', 1)
            operations = ['add', 'subtract', 'multiply', 'divide']
            operation = self.choose('Operation', operations, lambda x: x, default=1)
            return None if operation is None else {'a': a, 'b': b, 'operation': operation}
        if module_id == 'dice-roller':
            return {'count': self.integer('Dice count', 1, 1, 100),
                    'sides': self.integer('Sides per die', 6, 2, 1000)}
        if module_id == 'counter':
            action = self.choose('Counter action', ['get', 'increment', 'decrement', 'reset'], lambda x: x, default=1)
            return None if action is None else {'action': action}
        if module_id == 'slot-note':
            action = self.choose('Note action', ['get', 'set'], lambda x: x, default=1)
            if action is None: return None
            return {'action':'set', 'text':input('Note text: ')} if action == 'set' else {'action':'get'}
        if module_id == 'clock':
            return {}
        if module_id == 'theme-summary':
            return {}
        if module_id in ('empty', 'dashboard-health'):
            return {}
        raw = self.ask('Input JSON object', '{}')
        try:
            data = json.loads(raw)
            if not isinstance(data, dict): raise ValueError()
            json.dumps(data, allow_nan=False)
            return data
        except (TypeError, ValueError):
            raise ValueError('Input must be a valid JSON object.') from None

    def number(self, label, default):
        try:
            value = float(self.ask(label, default))
            if not math.isfinite(value): raise ValueError()
            return value
        except ValueError:
            raise ValueError('Enter a finite number.') from None

    def integer(self, label, default, minimum, maximum):
        try:
            value = int(self.ask(label, default))
            if not minimum <= value <= maximum: raise ValueError()
            return value
        except ValueError:
            raise ValueError(f'Enter an integer from {minimum} to {maximum}.') from None

    def slots_menu(self):
        result = self.call(self.slot_args('list'), state=True)
        if result is None: return
        self.slot_rows = result.get('slots', [])
        if not self.slot_rows:
            print('No slots are registered. Sign in to the Dashboard first.')
            return
        row = self.choose('Select a slot', self.slot_rows, lambda x: x['slot'] + '  |  ' + x['module_id'])
        if row is None: return
        slot, module = row['slot'], row['module_id']
        print(f'\n{slot}  |  {module}')
        action = self.choose('Slot actions', ['Read current value', 'Run module', 'Bind another module'], lambda x:x)
        if action == 'Read current value':
            self.show(self.call(self.slot_args('read', slot), state=True))
        elif action == 'Run module':
            data = self.input_for(module)
            if data is not None:
                self.show(self.call(self.slot_args('run', slot, '--input', json.dumps(data, ensure_ascii=False)), state=True))
        elif action == 'Bind another module':
            result = self.call(['modules', 'list'])
            if result is None: return
            selected = self.choose('Select a module', result.get('modules', []), lambda x:x['id'] + '  |  ' + x['name'])
            if selected is None: return
            context = {}
            if selected['id'] == 'clock':
                zone = self.ask('Time zone; leave blank for server time zone')
                if zone: context['timezone'] = zone
            elif selected['id'] == 'theme-summary':
                themes = sorted(p.stem for p in (Path(self.program).parent / 'modules/theme-summary/themes').glob('*.json'))
                theme = self.choose('Select a theme', themes, lambda x:x, default=1)
                if theme is None: return
                context['theme'] = theme
            self.show(self.call(self.slot_args('bind', slot, selected['id'], '--context', json.dumps(context)), state=True))
            updated = self.call(self.slot_args('list'), state=True, quiet=True)
            if updated is not None: self.slot_rows = updated.get('slots', [])

    def modules_menu(self):
        result = self.call(['modules', 'list'])
        if result is None: return
        self.module_rows = result.get('modules', [])
        row = self.choose('Select a module', self.module_rows, lambda x:x['id'] + '  |  ' + x['name'])
        if row is None: return
        module = row['id']
        print('\n' + row.get('description', ''))
        action = self.choose('Module actions', ['Run independently', 'Run with shared slot state'], lambda x:x)
        if action is None: return
        if action == 'Run with shared slot state':
            if module not in ('counter', 'slot-note'):
                print('Shared state is available for counter and slot-note. Use Slots to run other bound modules.')
                return
            result = self.call(self.slot_args('list'), state=True)
            if result is None: return
            rows = [item for item in result.get('slots', []) if item['module_id'] == module]
            slot = self.choose('Select a slot', rows, lambda x:x['slot'] + '  |  ' + x['module_id'])
            if slot is None: return
        data = self.input_for(module)
        if data is None: return
        args = ['modules', 'run', module, '--input', json.dumps(data, ensure_ascii=False)]
        if action == 'Run with shared slot state':
            args += ['--owner', self.owner, '--slot', slot['slot']]
        self.show(self.call(args, state=action == 'Run with shared slot state'))

    def executions_menu(self):
        result = self.call(self.worker_args('history'))
        if result is None: return
        rows = result.get('executions', [])
        row = self.choose('Recent executions', rows, lambda x:x.get('worker_id', '?') + '  |  ' + x.get('status', '?') + '  |  ' + x.get('execution_id', '?'))
        if row is None: return
        action = self.choose('Execution actions', ['Show details', 'Request cancellation'], lambda x:x)
        if action:
            self.show(self.call(self.worker_args('status' if action == 'Show details' else 'cancel', row['execution_id'])))

    def workers_menu(self):
        action = self.choose('Workers and executions', ['Select a Worker', 'Recent executions'], lambda x:x)
        if action == 'Recent executions':
            self.executions_menu(); return
        if action is None: return
        result = self.call(self.worker_args('list'))
        if result is None: return
        self.worker_rows = result.get('workers', [])
        row = self.choose('Select a Worker', self.worker_rows, lambda x:x['definition']['worker_id'] + '  |  ' + x['lifecycle'])
        if row is None: return
        worker = row['definition']['worker_id']
        action = self.choose('Worker actions', ['Show details', 'Run Worker', 'Enable', 'Disable'], lambda x:x)
        if action == 'Show details':
            self.show(self.call(self.worker_args('get', worker)))
        elif action == 'Run Worker':
            default = '{"values":[10,20,30]}' if worker == 'demo-summary' else '{}'
            raw = self.ask('Input JSON object', default)
            try:
                data = json.loads(raw)
                if not isinstance(data, dict): raise ValueError()
                data = json.dumps(data, ensure_ascii=False, allow_nan=False)
            except (TypeError, ValueError):
                print('Input must be a valid JSON object.', file=sys.stderr); return
            timeout = self.integer('Timeout in seconds', 30, 1, 300)
            print('A new idempotency key will be displayed. Keep it if the outcome is unknown.')
            self.show(self.call(self.worker_args('run', worker, '--input', data, '--timeout', str(timeout))))
        elif action in ('Enable', 'Disable'):
            self.show(self.call(self.worker_args(action.lower(), worker)))
            updated = self.call(self.worker_args('list'), quiet=True)
            if updated is not None: self.worker_rows = updated.get('workers', [])

    def run(self):
        try:
            self.refresh()
            while True:
                self.overview()
                choice = self.ask('Select a number', '0')
                if choice == '0': return 0
                try:
                    if choice == '1': self.slots_menu()
                    elif choice == '2': self.modules_menu()
                    elif choice == '3': self.workers_menu()
                    elif choice == '4': self.refresh()
                    elif choice == '5':
                        print('Slot owner and Worker token must refer to the same account.')
                        self.owner = self.ask('Slot owner', self.owner)
                        self.manager_url = self.ask('Manager HTTPS URL', self.manager_url)
                        self.token_file = self.ask('Private token file path', self.token_file)
                        self.ca_file = self.ask('CA bundle path', self.ca_file)
                        self.refresh()
                    else: print('Enter a number from the list.')
                except ValueError as error:
                    print(str(error), file=sys.stderr)
        except (EOFError, KeyboardInterrupt):
            print('\nExiting 30nA')
            return 0
