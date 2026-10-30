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

    def json_input(self, prompt='ورودی JSON object', default='{}'):
        raw = self.ask(prompt, default)
        try:
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError()
            return json.dumps(data, ensure_ascii=False, allow_nan=False)
        except (ValueError, TypeError):
            raise ValueError('ورودی باید یک JSON object معتبر باشد.') from None

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
                        print('اسلاتی برای این حساب ثبت نشده است؛ ابتدا در Dashboard وارد حساب شوید.')
                    for slot in output['slots']:
                        print(f"{slot['slot']}  |  {slot['module_id']}")
                elif isinstance(output, dict) and isinstance(output.get('modules'), list):
                    for module in output['modules']:
                        print(f"{module['id']}  |  {module['name']}")
                elif isinstance(output, dict) and isinstance(output.get('workers'), list):
                    if not output['workers']:
                        print('Worker ثبت‌شده‌ای برای این حساب وجود ندارد.')
                    for worker in output['workers']:
                        print(f"{worker['definition']['worker_id']}  |  {worker['lifecycle']}")
                else:
                    print(json.dumps(output, ensure_ascii=False, indent=2))
        if completed.returncode:
            print('عملیات انجام نشد.', file=sys.stderr)
        return completed.returncode

    def slot_args(self, *args):
        return ['slots', '--owner', self.owner, *args]

    def worker_args(self, *args):
        return ['workers', '--manager-url', self.manager_url, '--token-file', self.token_file,
                '--ca-file', self.ca_file, *args]

    def run(self):
        print('30nA — مدیریت اسلات، ماژول و Worker')
        print('وضعیت اسلات‌ها متعلق به owner انتخاب‌شده است؛ Workerها با فایل token احراز هویت می‌شوند.')
        while True:
            print(f'\nحساب اسلات: {self.owner}')
            print('۱. فهرست اسلات‌ها       ۲. خواندن اسلات        ۳. اجرای اسلات')
            print('۴. اتصال ماژول به اسلات   ۵. فهرست ماژول‌ها      ۶. اجرای ماژول')
            print('۷. فهرست Workerها        ۸. اجرای Worker        ۹. وضعیت اجرا')
            print('۱۰. لغو اجرا             ۱۱. تنظیم حساب و اتصال  ۰. خروج')
            try:
                choice = self.ask('انتخاب').translate(str.maketrans('۰۱۲۳۴۵۶۷۸۹', '0123456789'))
                if choice in ('0', 'q', 'exit'):
                    return 0
                if choice == '1':
                    self.call(self.slot_args('list'), state=True)
                elif choice == '2':
                    self.call(self.slot_args('read', self.ask('شناسه اسلات، مانند slot-04')), state=True)
                elif choice == '3':
                    slot = self.ask('شناسه اسلات')
                    data = self.json_input()
                    self.call(self.slot_args('run', slot, '--input', data), state=True)
                elif choice == '4':
                    slot = self.ask('شناسه اسلات')
                    module = self.ask('شناسه ماژول')
                    context = self.json_input('تنظیمات اسلات، مانند timezone یا theme')
                    self.call(self.slot_args('bind', slot, module, '--context', context), state=True)
                elif choice == '5':
                    self.call(['modules', 'list'])
                elif choice == '6':
                    module = self.ask('شناسه ماژول')
                    data = self.json_input()
                    args = ['modules', 'run', module, '--input', data]
                    shared = False
                    if module in ('counter', 'slot-note'):
                        slot = self.ask('شناسه اسلات برای وضعیت مشترک؛ برای اجرای مستقل خالی بگذارید')
                        if slot:
                            args += ['--owner', self.owner, '--slot', slot]
                            shared = True
                    self.call(args, state=shared)
                elif choice == '7':
                    self.call(self.worker_args('list'))
                elif choice == '8':
                    worker = self.ask('شناسه Worker')
                    data = self.json_input()
                    timeout = self.ask('حداکثر زمان اجرا به ثانیه', '30')
                    key = self.ask('idempotency key قبلی برای تکرار همان درخواست؛ در غیر این صورت خالی')
                    args = ['run', worker, '--input', data, '--timeout', timeout]
                    if key:
                        args += ['--idempotency-key', key]
                    self.call(self.worker_args(*args))
                elif choice in ('9', '10'):
                    execution_id = self.ask('شناسه اجرا')
                    self.call(self.worker_args('status' if choice == '9' else 'cancel', execution_id))
                elif choice == '11':
                    print('شناسه owner اسلات و صاحب token برای Worker باید به یک حساب اشاره کنند.')
                    self.owner = self.ask('owner اسلات', self.owner)
                    self.manager_url = self.ask('آدرس HTTPS Manager', self.manager_url)
                    self.token_file = self.ask('مسیر فایل خصوصی token', self.token_file)
                    self.ca_file = self.ask('مسیر CA bundle', self.ca_file)
                else:
                    print('گزینه معتبر را انتخاب کنید.')
            except ValueError as error:
                print(str(error), file=sys.stderr)
            except (EOFError, KeyboardInterrupt):
                print('\nخروج از 30nA')
                return 0
