"""Interactive terminal interface over the existing 30na commands."""
import json
import os
from pathlib import Path
import subprocess
import sys


class Terminal:
    def __init__(self, owner='customer', manager_url='https://localhost:18444',
                 token_file='/etc/30na/customer-token', ca_file='/etc/30na/ca/trust.pem'):
        self.owner = owner
        self.manager_url = manager_url
        self.token_file = token_file
        self.ca_file = ca_file
        self.program = str(Path(__file__).resolve().parent / '30na')

    def ask(self, prompt, default=None):
        suffix = f' [{default}]' if default is not None else ''
        value = input(prompt + suffix + ': ').strip()
        return value if value else (default if default is not None else '')

    def json_input(self, prompt='JSON object input', default='{}'):
        raw = self.ask(prompt, default)
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError()
            return json.dumps(data, ensure_ascii=False, allow_nan=False)
        except (ValueError, TypeError):
            raise ValueError('Input must be a valid JSON object.') from None

    def call(self, args, *, state=False):
        command = [sys.executable, self.program, *args]
        if state and os.geteuid() == 0:
            command = ['runuser', '-u', '30na', '--', *command]
        completed = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if completed.stderr:
            print(completed.stderr.rstrip(), file=sys.stderr)
        if completed.stdout:
            try:
                output = json.loads(completed.stdout)
            except ValueError:
                print(completed.stdout.rstrip())
            else:
                if isinstance(output, dict) and isinstance(output.get('slots'), list):
                    if not output['slots']:
                        print('No slots are registered for this account; sign in to the Dashboard first.')
                    for slot in output['slots']:
                        print(f"{slot['slot']}  |  {slot['module_id']}")
                elif isinstance(output, dict) and isinstance(output.get('modules'), list):
                    for module in output['modules']:
                        print(f"{module['id']}  |  {module['name']}")
                elif isinstance(output, dict) and isinstance(output.get('workers'), list):
                    if not output['workers']:
                        print('No Workers are registered for this account.')
                    for worker in output['workers']:
                        print(f"{worker['definition']['worker_id']}  |  {worker['lifecycle']}")
                else:
                    print(json.dumps(output, ensure_ascii=False, indent=2))
        if completed.returncode:
            print('Operation failed.', file=sys.stderr)
        return completed.returncode

    def slot_args(self, *args):
        return ['slots', '--owner', self.owner, *args]

    def worker_args(self, *args):
        return ['workers', '--manager-url', self.manager_url, '--token-file', self.token_file,
                '--ca-file', self.ca_file, *args]

    def run(self):
        print('30nA - Slots, modules, and Workers')
        print('Slots use the selected owner; Workers authenticate with the token file.')
        while True:
            print(f'\nSlot owner: {self.owner}')
            print('1. List slots         2. Read slot           3. Run slot')
            print('4. Bind slot          5. List modules        6. Run module')
            print('7. List Workers       8. Run Worker          9. Execution status')
            print('10. Cancel execution  11. Account and connection  0. Exit')
            try:
                choice = self.ask('Choice')
                if choice in ('0', 'q', 'exit'):
                    return 0
                if choice == '1':
                    self.call(self.slot_args('list'), state=True)
                elif choice == '2':
                    self.call(self.slot_args('read', self.ask('Slot ID, e.g. slot-04')), state=True)
                elif choice == '3':
                    slot = self.ask('Slot ID')
                    data = self.json_input()
                    self.call(self.slot_args('run', slot, '--input', data), state=True)
                elif choice == '4':
                    slot = self.ask('Slot ID')
                    module = self.ask('Module ID')
                    context = self.json_input('Slot context, such as timezone or theme')
                    self.call(self.slot_args('bind', slot, module, '--context', context), state=True)
                elif choice == '5':
                    self.call(['modules', 'list'])
                elif choice == '6':
                    module = self.ask('Module ID')
                    data = self.json_input()
                    args = ['modules', 'run', module, '--input', data]
                    shared = False
                    if module in ('counter', 'slot-note'):
                        slot = self.ask('Slot ID for shared state; leave blank for standalone execution')
                        if slot:
                            args += ['--owner', self.owner, '--slot', slot]
                            shared = True
                    self.call(args, state=shared)
                elif choice == '7':
                    self.call(self.worker_args('list'))
                elif choice == '8':
                    worker = self.ask('Worker ID')
                    data = self.json_input()
                    timeout = self.ask('Execution timeout in seconds', '30')
                    key = self.ask('Previous idempotency key to retry the same request; otherwise leave blank')
                    args = ['run', worker, '--input', data, '--timeout', timeout]
                    if key:
                        args += ['--idempotency-key', key]
                    self.call(self.worker_args(*args))
                elif choice in ('9', '10'):
                    execution_id = self.ask('Execution ID')
                    self.call(self.worker_args('status' if choice == '9' else 'cancel', execution_id))
                elif choice == '11':
                    print('Slot owner and Worker token must refer to the same account.')
                    self.owner = self.ask('Slot owner', self.owner)
                    self.manager_url = self.ask('Manager HTTPS URL', self.manager_url)
                    self.token_file = self.ask('Private token file path', self.token_file)
                    self.ca_file = self.ask('CA bundle path', self.ca_file)
                else:
                    print('Choose a valid option.')
            except ValueError as error:
                print(str(error), file=sys.stderr)
            except (EOFError, KeyboardInterrupt):
                print('\nExiting 30nA')
                return 0
