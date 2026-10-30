"""Numbered interactive workspace over the same 30na CLI used in scripts."""
import json
import math
import os
from pathlib import Path
import subprocess
import shutil
import sys


class Terminal:
    def __init__(self, owner='customer', manager_url='https://localhost:18444',
                 token_file='/etc/30na/customer-token', ca_file='/etc/30na/ca/trust.pem'):
        self.owner, self.manager_url = owner, manager_url
        self.token_file, self.ca_file = token_file, ca_file
        self.program = str(Path(__file__).resolve().parent / '30na')
        self.slot_rows, self.module_rows, self.worker_rows = None, None, None
        self.health = None
        self.notice = None
        self.path = ['Main menu']
        self.selected_number = None
        self.color = sys.stdout.isatty() and os.environ.get('TERM', '') != 'dumb' and 'NO_COLOR' not in os.environ

    def style(self, text, *codes):
        if not self.color:
            return str(text)
        return '\033[' + ';'.join(codes) + 'm' + str(text) + '\033[0m'

    def ask(self, label, default=None):
        suffix = f' [{default}]' if default is not None else ''
        value = input(self.style(label, '1', '36') + self.style(suffix, '2') + ': ').strip()
        return value if value else (str(default) if default is not None else '')

    def choose(self, title, rows, label, default=0):
        while True:
            self.screen(title)
            current_rows = rows() if callable(rows) else rows
            if not current_rows:
                print('No items available.')
                self.ask('Press Enter to continue')
                return None
            for index, row in enumerate(current_rows, 1):
                print('  ' + self.style(f'{index:>2}.', '1', '36') + ' ' + str(label(row)))
            print('  ' + self.style(' 0.', '1', '36') + ' Back')
            value = self.ask('Select a number (example: 1)', str(default))
            if value == '0': return None
            if value.isascii() and value.isdigit() and 1 <= int(value) <= len(current_rows):
                self.selected_number = int(value)
                return current_rows[int(value) - 1]
            self.notice = 'Enter a number from the list.'

    def call(self, args, *, state=False, quiet=False):
        command = [sys.executable, self.program, *args]
        if state and os.geteuid() == 0:
            command = ['runuser', '-u', '30na', '--', *command]
        try:
            completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        except OSError:
            if not quiet: self.notice = 'Could not start the command.'
            return None
        if completed.returncode:
            if not quiet:
                self.notice = completed.stderr.rstrip() or 'Operation failed.'
            return None
        if completed.stderr and not quiet:
            self.notice = completed.stderr.rstrip()
        try:
            return json.loads(completed.stdout)
        except ValueError:
            if not quiet: self.notice = 'Invalid response from command.'
            return None

    def show(self, value):
        if value is not None:
            self.screen('Result')
            if isinstance(value, dict) and 'slot' in value and 'module_id' in value and 'result' in value:
                print(self.style('Slot:', '1') + f" {value['slot']}  |  " + self.style('Module:', '1') + f" {value['module_id']}")
                if value.get('context'):
                    print('Context: ' + json.dumps(value['context'], ensure_ascii=False))
                print(json.dumps(value['result'], ensure_ascii=False, indent=2))
            else:
                print(json.dumps(value, ensure_ascii=False, indent=2))
            self.ask('Press Enter to continue')

    def slot_args(self, *args):
        return ['slots', '--owner', self.owner, *args]

    def worker_args(self, *args):
        return ['workers', '--manager-url', self.manager_url, '--token-file', self.token_file,
                '--ca-file', self.ca_file, *args]

    def refresh(self):
        slots = self.call(self.slot_args('list'), state=True, quiet=True)
        modules = self.call(['modules', 'list'], quiet=True)
        workers = self.call(self.worker_args('list'), quiet=True)
        health = self.call(['modules', 'run', 'dashboard-health'], quiet=True)
        self.slot_rows = slots.get('slots', []) if isinstance(slots, dict) else None
        self.module_rows = modules.get('modules', []) if isinstance(modules, dict) else None
        self.worker_rows = workers.get('workers', []) if isinstance(workers, dict) else None
        self.health = health.get('status', 'unknown') if isinstance(health, dict) else 'unavailable'

    def screen(self, title=None):
        self.refresh()
        if sys.stdout.isatty() and os.environ.get('TERM') != 'dumb':
            sys.stdout.write('\033[2J\033[H')
            sys.stdout.flush()
        else:
            print('\n')
        width = max(20, min(shutil.get_terminal_size((100, 24)).columns, 160))
        count = lambda value: str(len(value)) if value is not None else 'unavailable'
        enabled = sum(row.get('lifecycle') == 'enabled' for row in (self.worker_rows or []))
        print(self.style('=' * width, '36'))
        print(self.style('30nA STATUS', '1', '36') + self.style('  |  v0.1.2 (preview)', '2') + '  |  Owner: ' + self.style(self.owner, '1'))
        health_color = '32' if str(self.health).lower() in ('ok', 'healthy', 'up') else '33'
        print('Dashboard: ' + self.style(self.health, '1', health_color) + f'  |  Slots: {count(self.slot_rows)}  |  Modules: {count(self.module_rows)}  |  Workers: {count(self.worker_rows)}' + (f' ({enabled} enabled)' if self.worker_rows is not None else ''))
        print(self.style('-' * width, '2'))
        print(self.style('SLOTS', '1', '36'))
        if self.slot_rows is None:
            print('  Unavailable')
        elif not self.slot_rows:
            print('  No slots registered. Sign in to the Dashboard first.')
        else:
            items = [f"{i}. {row['slot']} | {row['module_id']}" for i, row in enumerate(self.slot_rows, 1)]
            cell = max(len(item) for item in items) + 3
            columns = max(1, min(3, width // cell))
            for offset in range(0, len(items), columns):
                group = items[offset:offset + columns]
                cells = []
                for i, item in enumerate(group):
                    number, details = item.split('. ', 1)
                    slot_id, module_id = details.split(' | ', 1)
                    formatted = self.style(number + '.', '1', '36') + ' ' + self.style(slot_id, '1') + ' | ' + self.style(module_id, '2' if module_id == 'empty' else '37')
                    cells.append(formatted + (' ' * (cell - len(item)) if i < len(group) - 1 else ''))
                print(''.join(cells))
        print(self.style('-' * width, '2'))
        print(self.style('WORKERS', '1', '36'))
        if self.worker_rows is None:
            print('  Unavailable')
        elif not self.worker_rows:
            print('  No Workers registered.')
        else:
            for index, worker in enumerate(self.worker_rows, 1):
                lifecycle = worker['lifecycle']
                print('  ' + self.style(f'{index}.', '1', '36') + f" {worker['definition']['worker_id']} | " + self.style(lifecycle, '32' if lifecycle == 'enabled' else '33'))
        print(self.style('=' * width, '36'))
        print(self.style('Path: ', '1') + self.style(' > '.join(self.path + ([title] if title and title.lower() != self.path[-1].lower() else [])), '36'))
        if title:
            print('\n' + self.style(title, '1', '36'))
        if self.notice:
            print(self.style(self.notice, '1', '33'))
            self.notice = None

    def overview(self):
        self.screen('MAIN MENU')
        for number, label in enumerate(['Slots', 'Modules', 'Workers and executions', 'Refresh status', 'Account and connection settings'], 1):
            print('  ' + self.style(f'{number}.', '1', '36') + ' ' + label)
        print('  ' + self.style('0.', '1', '36') + ' Exit')

    def input_for(self, module_id):
        self.screen('INPUT - ' + module_id)
        if module_id == 'calculator':
            a = self.number('First number', 0)
            b = self.number('Second number', 1)
            operations = ['add', 'subtract', 'multiply', 'divide']
            operation = self.choose(f'Operation for {a} and {b}', operations, lambda x: x, default=1)
            if operation is not None: self.path = self.path + [f'{self.selected_number}. {operation}']
            return None if operation is None else {'a': a, 'b': b, 'operation': operation}
        if module_id == 'dice-roller':
            return {'count': self.integer('Dice count', 1, 1, 100),
                    'sides': self.integer('Sides per die', 6, 2, 1000)}
        if module_id == 'counter':
            action = self.choose('Counter action', ['get', 'increment', 'decrement', 'reset'], lambda x: x, default=1)
            if action is not None: self.path = self.path + [f'{self.selected_number}. {action}']
            return None if action is None else {'action': action}
        if module_id == 'slot-note':
            action = self.choose('Note action', ['get', 'set'], lambda x: x, default=1)
            if action is None: return None
            self.path = self.path + [f'{self.selected_number}. {action}']
            if action == 'set':
                self.screen('SET NOTE')
                return {'action':'set', 'text':self.ask('Note text (example: Server maintenance at 18:00)')}
            return {'action':'get'}
        if module_id == 'clock':
            return {}
        if module_id == 'theme-summary':
            return {}
        if module_id in ('empty', 'dashboard-health'):
            return {}
        raw = self.ask('Input JSON object (example: {"key":"value"})', '{}')
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
        while True:
            self.path = ['Main menu', '1. Slots']
            row = self.choose('Select a slot', lambda: self.slot_rows or [], lambda x: x['slot'] + '  |  ' + x['module_id'])
            if row is None: return
            slot = row['slot']
            slot_path = self.path + [f'{self.selected_number}. {slot}']
            while True:
                self.path = slot_path
                # The binding may have changed in the Dashboard or after a bind.
                self.refresh()
                current = next((item for item in (self.slot_rows or []) if item['slot'] == slot), None)
                if current is None:
                    self.notice = 'Slot is no longer available.'
                    break
                module = current['module_id']
                action = self.choose('Slot actions - ' + slot + ' | ' + module,
                                     ['Read current value', 'Run module', 'Bind another module'], lambda x: x)
                if action is None: break
                self.path = slot_path + [f'{self.selected_number}. {action}']
                try:
                    if action == 'Read current value':
                        self.show(self.call(self.slot_args('read', slot), state=True))
                    elif action == 'Run module':
                        data = self.input_for(module)
                        if data is not None:
                            self.show(self.call(self.slot_args('run', slot, '--input', json.dumps(data, ensure_ascii=False), '--expect-module', module), state=True))
                    else:
                        selected = self.choose('Select a module', lambda: self.module_rows or [], lambda x: x['id'] + '  |  ' + x['name'])
                        if selected is None: continue
                        self.path = self.path + [f"{self.selected_number}. {selected['id']}"]
                        context = {}
                        if selected['id'] == 'clock':
                            self.screen('Bind module')
                            zone = self.ask('Time zone (example: Asia/Tehran; Enter for server time zone)')
                            if zone: context['timezone'] = zone
                        elif selected['id'] == 'theme-summary':
                            themes = sorted(p.stem for p in (Path(self.program).parent / 'modules/theme-summary/themes').glob('*.json'))
                            theme = self.choose('Select a theme', themes, lambda x: x, default=1)
                            if theme is None: continue
                            self.path = self.path + [f'{self.selected_number}. {theme}']
                            context['theme'] = theme
                        self.show(self.call(self.slot_args('bind', slot, selected['id'], '--context', json.dumps(context)), state=True))
                except ValueError as error:
                    self.notice = str(error)

    def modules_menu(self):
        while True:
            self.path = ['Main menu', '2. Modules']
            row = self.choose('Select a module', lambda: self.module_rows or [], lambda x: x['id'] + '  |  ' + x['name'])
            if row is None: return
            module = row['id']
            module_path = self.path + [f'{self.selected_number}. {module}']
            while True:
                self.path = module_path
                action = self.choose('Module actions - ' + module, ['Run independently', 'Run with shared slot state'], lambda x: x)
                if action is None: break
                self.path = module_path + [f'{self.selected_number}. {action}']
                try:
                    slot = None
                    if action == 'Run with shared slot state':
                        if module not in ('counter', 'slot-note'):
                            self.notice = 'Shared state is available for counter and slot-note. Use Slots for other bound modules.'
                            continue
                        slot = self.choose('Select a slot', lambda: [item for item in (self.slot_rows or []) if item['module_id'] == module], lambda x: x['slot'] + '  |  ' + x['module_id'])
                        if slot is None: continue
                        self.path = self.path + [f"{self.selected_number}. {slot['slot']}"]
                    data = self.input_for(module)
                    if data is None: continue
                    args = ['modules', 'run', module, '--input', json.dumps(data, ensure_ascii=False)]
                    if slot is not None:
                        args += ['--owner', self.owner, '--slot', slot['slot']]
                    self.show(self.call(args, state=slot is not None))
                except ValueError as error:
                    self.notice = str(error)

    def executions_menu(self):
        base_path = self.path + ['2. Recent executions']
        while True:
            self.path = base_path
            result = self.call(self.worker_args('history'))
            if result is None: return
            row = self.choose('Recent executions', result.get('executions', []), lambda x: x.get('worker_id', '?') + '  |  ' + x.get('status', '?') + '  |  ' + x.get('execution_id', '?'))
            if row is None: return
            execution_path = base_path + [f"{self.selected_number}. {row['execution_id']}"]
            while True:
                self.path = execution_path
                action = self.choose('Execution actions', ['Show details', 'Request cancellation'], lambda x: x)
                if action is None: break
                self.path = execution_path + [f'{self.selected_number}. {action}']
                self.show(self.call(self.worker_args('status' if action == 'Show details' else 'cancel', row['execution_id'])))

    def workers_menu(self):
        base_path = ['Main menu', '3. Workers and executions']
        while True:
            self.path = base_path
            action = self.choose('Workers and executions', ['Select a Worker', 'Recent executions'], lambda x: x)
            if action is None: return
            if action == 'Recent executions':
                self.executions_menu()
                continue
            while True:
                self.path = base_path + ['1. Select a Worker']
                row = self.choose('Select a Worker', lambda: self.worker_rows or [], lambda x: x['definition']['worker_id'] + '  |  ' + x['lifecycle'])
                if row is None: break
                worker = row['definition']['worker_id']
                worker_path = self.path + [f'{self.selected_number}. {worker}']
                while True:
                    self.path = worker_path
                    action = self.choose('Worker actions - ' + worker, ['Show details', 'Run Worker', 'Enable', 'Disable'], lambda x: x)
                    if action is None: break
                    self.path = worker_path + [f'{self.selected_number}. {action}']
                    try:
                        if action == 'Show details':
                            self.show(self.call(self.worker_args('get', worker)))
                        elif action == 'Run Worker':
                            self.screen('Run Worker')
                            default = '{"values":[10,20,30]}' if worker == 'demo-summary' else '{}'
                            raw = self.ask('Input JSON object (example: {"key":"value"})', default)
                            try:
                                data = json.loads(raw)
                                if not isinstance(data, dict): raise ValueError()
                                data = json.dumps(data, ensure_ascii=False, allow_nan=False)
                            except (TypeError, ValueError):
                                raise ValueError('Input must be a valid JSON object.') from None
                            timeout = self.integer('Timeout in seconds (example: 30)', 30, 1, 300)
                            self.show(self.call(self.worker_args('run', worker, '--input', data, '--timeout', str(timeout))))
                        else:
                            self.show(self.call(self.worker_args(action.lower(), worker)))
                    except ValueError as error:
                        self.notice = str(error)

    def run(self):
        try:
            while True:
                self.path = ['Main menu']
                self.overview()
                choice = self.ask('Select a number (example: 1)', '0')
                if choice == '0': return 0
                try:
                    if choice == '1': self.slots_menu()
                    elif choice == '2': self.modules_menu()
                    elif choice == '3': self.workers_menu()
                    elif choice == '4': pass
                    elif choice == '5':
                        self.path = ['Main menu', '5. Account and connection settings']
                        self.screen('Account and connection settings')
                        print('Settings apply only to this CLI session. Press Enter to keep each current value.')
                        print('Slot owner selects whose slots are shown. Worker access uses the token file and Manager URL.')
                        print('The token must belong to the selected account. The CA bundle verifies the Manager certificate.')
                        self.owner = self.ask('Slot owner (example: customer)', self.owner)
                        self.manager_url = self.ask('Manager HTTPS URL (example: https://localhost:18444)', self.manager_url)
                        self.token_file = self.ask('Token file path (example: /etc/30na/customer-token)', self.token_file)
                        self.ca_file = self.ask('CA bundle path (example: /etc/30na/ca/trust.pem)', self.ca_file)
                    else: self.notice = 'Enter a number from the list.'
                except ValueError as error:
                    self.notice = str(error)
        except (EOFError, KeyboardInterrupt):
            print('\nExiting 30nA')
            return 0
