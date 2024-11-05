import cmd
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import colorama
from colorama import Fore, Style
import concurrent.futures
from datetime import datetime
import subprocess
import shutil
import paramiko
import json 
from threading import Lock
import requests
colorama.init()

## Constants
MOD_DIR = Path.home() / '.pyhunter3/modules'
LOG_DIR = Path.home() / '.pyhunter3/logs'
REPORT_DIR = Path.home() / '.pyhunter3/reports'


@dataclass
class ModuleResult:
    module_name: str
    start_time: datetime
    end_time: datetime
    status: str
    output: str
    parameters: dict
    runtime: str
    log_file: str


@dataclass
class ModuleParameter:
    name: str
    description: str
    required: bool = False
    default: Optional[str] = None
    value: Optional[str] = None

@dataclass
class Module:
    name: str
    description: str
    author: str
    parameters: List[ModuleParameter]
    category: str
    path: str
    dependencies: List[str] = None
    install_command: str = ""


@dataclass
class SSHConnection:
    hostname: str
    username: str
    port: int = 22
    key_path: Optional[str] = None
    password: Optional[str] = None
    client: Optional[paramiko.SSHClient] = None
    connected: bool = False

@dataclass
class ModuleStatus:
    start_time: datetime
    is_running: bool
    last_update: str = ""
    progress: int = 0
    total_tasks: int = 0
    parameters: Dict[str, Any] = None


class ReportGenerator:
    def __init__(self, reports_dir: str):
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)
        
        # Initialize Jinja2 environment
        self.css = """
        :root {
            --bg-primary: #1a1b1e;
            --bg-secondary: #2c2e33;
            --bg-tertiary: #373a40;
            --text-primary: #e4e6ea;
            --text-secondary: #a1a5ab;
            --accent-primary: #4dabf7;
            --accent-secondary: #339af0;
            --success-color: #40c057;
            --error-color: #fa5252;
            --warning-color: #fab005;
            --border-radius: 8px;
            --transition-speed: 0.2s;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: var(--bg-primary);
            color: var(--text-primary);
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: var(--bg-secondary);
            padding: 24px;
            border-radius: var(--border-radius);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        }

        .header {
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            color: white;
            padding: 24px;
            border-radius: var(--border-radius) var(--border-radius) 0 0;
            margin: -24px -24px 24px -24px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .header h1 {
            margin: 0;
            font-size: 2em;
            font-weight: 700;
        }

        .summary {
            background-color: var(--bg-tertiary);
            padding: 20px;
            border-radius: var(--border-radius);
            margin-bottom: 24px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .summary h2 {
            margin-top: 0;
            color: var(--accent-primary);
        }

        pre {
            background-color: var(--bg-tertiary);
            padding: 16px;
            border-radius: var(--border-radius);
            overflow-x: auto;
            border: 1px solid rgba(255, 255, 255, 0.1);
            margin: 16px 0;
        }

        code {
            background-color: var(--bg-tertiary);
            padding: 3px 6px;
            border-radius: 4px;
            font-family: 'Fira Code', 'Cascadia Code', 'Source Code Pro', monospace;
            font-size: 0.9em;
        }

        h1, h2, h3, h4, h5, h6 {
            color: var(--text-primary);
            margin-top: 1.5em;
            margin-bottom: 0.75em;
        }

        p {
            color: var(--text-secondary);
            margin: 1em 0;
        }

        ul, ol {
            color: var(--text-secondary);
            padding-left: 1.5em;
        }

        a {
            color: var(--accent-primary);
            text-decoration: none;
            transition: color var(--transition-speed) ease;
        }

        a:hover {
            color: var(--accent-secondary);
            text-decoration: underline;
        }

        /* Status colors */
        .status-success {
            color: var(--success-color);
        }

        .status-error {
            color: var(--error-color);
        }

        .status-running {
            color: var(--warning-color);
        }

        /* Module results styling */
        .module-result {
            background-color: var(--bg-tertiary);
            border-radius: var(--border-radius);
            margin-bottom: 20px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: transform var(--transition-speed) ease;
        }

        .module-result:hover {
            transform: translateY(-2px);
        }

        .module-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
            padding-bottom: 16px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .module-content {
            color: var(--text-secondary);
        }

        /* Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
            background-color: var(--bg-tertiary);
            border-radius: var(--border-radius);
            overflow: hidden;
        }

        th, td {
            padding: 12px 16px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        th {
            background-color: var(--bg-secondary);
            color: var(--text-primary);
            font-weight: 600;
        }

        tr:last-child td {
            border-bottom: none;
        }

        /* Scrollbar styling */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-secondary);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--bg-tertiary);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--accent-primary);
        }

        /* Print styles */
        @media print {
            body {
                background-color: white;
                color: black;
            }

            .container {
                box-shadow: none;
            }

            pre, code {
                border: 1px solid #ddd;
            }
        }
        """

    def _load_module_results(self, logs_dir: str, module_status: Dict) -> List[ModuleResult]:
        """Load and parse module results from log files"""
        results = []
        for module_name, status in module_status.items():
            # Find the most recent log file for this module using timestamp pattern
            log_files = sorted(
                Path(logs_dir).glob(f"{module_name}_*.log"),  # Changed from f"{module_name}.log"
                key=os.path.getmtime,
                reverse=True
            )
            
            if log_files and status:
                log_file = log_files[0]
                try:
                    with open(log_file, 'r') as f:
                        output = f.read()

                    # Calculate times based on module status and file timestamp
                    start_time = status.start_time
                    end_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                    runtime = end_time - start_time

                    # Create ModuleResult with actual parameter values from status
                    result = ModuleResult(
                        module_name=module_name,
                        start_time=start_time,
                        end_time=end_time,
                        status="Completed" if not status.is_running else "Running",
                        output=output,
                        parameters=status.parameters if status.parameters else {},
                        runtime=str(runtime).split('.')[0],
                        log_file=str(log_file)
                    )
                    results.append(result)
                except Exception as e:
                    print(f"Error loading results for {module_name}: {str(e)}")

        return results

    def generate_markdown(self, logs_dir: str, module_status: Dict) -> str:
        """Generate markdown report from module results"""
        results = self._load_module_results(logs_dir, module_status)
        
        if not results:
            return "# Pyhunter Report\nNo module results found."
        
        # Calculate summary statistics
        total_modules = len(results)
        successful_modules = sum(1 for r in results if "error" not in r.output.lower())
        failed_modules = total_modules - successful_modules
        
        markdown_content = f"""
# Pyhunter Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Test Summary
- Total Modules Run: {total_modules}
- Successful: {successful_modules}
- Failed: {failed_modules}

## Module Results
"""

        for result in results:
            markdown_content += f"""
### {result.module_name}
- Status: {result.status}
- Start Time: {result.start_time}
- End Time: {result.end_time}
- Runtime: {result.runtime}

#### Parameters
```json
{json.dumps(result.parameters, indent=2)}
```

#### Output
```
{result.output}
```

Log File: {result.log_file}

---
"""
        
        return markdown_content

    

    def generate_html(self, markdown_content: str, module_status: Dict) -> str:
        """Generate HTML report from markdown content"""
        try:
            import markdown
            
            html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pyhunter Report</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/inter-ui/3.19.3/inter.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/fira-code/6.2.0/fira_code.min.css">
    <style>
        {self.css}
    </style>
</head>
<body>
    <div class="container">
        {markdown.markdown(markdown_content, extensions=['fenced_code', 'tables'])}
    </div>
</body>
</html>
"""
            return html_template
            
        except ImportError:
            return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pyhunter Report</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/inter-ui/3.19.3/inter.min.css">
    <style>
        {self.css}
    </style>
</head>
<body>
    <div class="container">
        <pre>{markdown_content}</pre>
    </div>
</body>
</html>
"""

class ModuleBuilder:
    def __init__(self):
        self.modules_dir = os.path.expanduser(MOD_DIR)
        
    def build_module(self, file_path: str, build_tags: str = "") -> bool:
        """Build a single module and return whether it was successful"""
        try:
            if not file_path.endswith(".go"):  # Ensure only .go files are processed
                return False
            
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            output_path = os.path.join(self.modules_dir, f"{module_name}_module")
            if os.name == 'nt':  # Windows
                output_path += '.exe'
            
            # Prepare the command with optional build tags
            command = ["go", "build"]
            if build_tags:
                command.extend(["-tags", build_tags])
            command.extend(["-o", output_path, file_path])

            result = subprocess.run(
                command,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # print(f"{Fore.GREEN}Successfully built module: {module_name}{Style.RESET_ALL}")
                return True  # Successful build
            else:
                print(f"{Fore.RED}Failed to build module {module_name}: {result.stderr}{Style.RESET_ALL}")
                return False  # Failed build

        except Exception as e:
            print(f"{Fore.RED}Error building module {file_path}: {str(e)}{Style.RESET_ALL}")
            return False  # Exception indicates failure

    def build_all_modules(self) -> bool:
        """Build all modules in the modules directory and provide a summary"""
        successful_builds = 0
        failed_builds = 0
        success = True

        if not os.path.exists(self.modules_dir):
            os.makedirs(self.modules_dir)

        # Only consider .go files for building
        for file_path in Path(self.modules_dir).glob("*.go"):
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            build_tags = module_name
            if self.build_module(str(file_path), build_tags):
                successful_builds += 1  # Increment success counter
            else:
                failed_builds += 1  # Increment failure counter
                success = False  # Mark overall success as False if any module fails

        # Print the summary of builds
        print(f"{Fore.GREEN}Build Summary: {successful_builds} modules built successfully, {failed_builds} failed.{Style.RESET_ALL}")

        return success
    
    def check_if_built(self, module_path: str) -> bool:
        """Check if a module has been built"""
        if module_path.endswith(".go"):
            module_name = os.path.splitext(os.path.basename(module_path))[0]
            binary_name = f"{module_name}_module"
            if os.name == 'nt':
                binary_name += '.exe'
            
            binary_path = os.path.join(self.modules_dir, binary_name)
            return os.path.exists(binary_path)
            
        return True
    

class SSHHandler:
    def __init__(self):
        self.connection: Optional[SSHConnection] = None
        self.remote_modules_path = MOD_DIR
    
    def connect(self, hostname: str, username: str, password: str = None, 
                key_path: str = None, port: int = 22) -> bool:
        """Establish SSH connection to remote host"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            connect_kwargs = {
                "hostname": hostname,
                "username": username,
                "port": port
            }
            
            if password:
                connect_kwargs["password"] = password
            elif key_path:
                connect_kwargs["key_filename"] = os.path.expanduser(key_path)
            
            client.connect(**connect_kwargs)
            
            self.connection = SSHConnection(
                hostname=hostname,
                username=username,
                port=port,
                key_path=key_path,
                password=password,
                client=client,
                connected=True
            )
            
            # Ensure remote modules directory exists
            self.execute_command(f"mkdir -p {self.remote_modules_path}")
            return True
            
        except Exception as e:
            print(f"{Fore.RED}SSH connection failed: {str(e)}{Style.RESET_ALL}")
            return False
    
    def disconnect(self):
        """Close SSH connection"""
        if self.connection and self.connection.client:
            self.connection.client.close()
            self.connection.connected = False
            self.connection = None
    
    def execute_command(self, command: str) -> tuple[str, str]:
        """Execute command on remote host"""
        if not self.connection or not self.connection.connected:
            raise Exception("Not connected to remote host")
            
        stdin, stdout, stderr = self.connection.client.exec_command(command)
        return stdout.read().decode(), stderr.read().decode()
    
    def upload_file(self, local_path: str, remote_path: str):
        """Upload file to remote host"""
        if not self.connection or not self.connection.connected:
            raise Exception("Not connected to remote host")
            
        sftp = self.connection.client.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()
    
    def download_file(self, remote_path: str, local_path: str):
        """Download file from remote host"""
        if not self.connection or not self.connection.connected:
            raise Exception("Not connected to remote host")
            
        sftp = self.connection.client.open_sftp()
        sftp.get(remote_path, local_path)
        sftp.close()

class WebTestConsole(cmd.Cmd):
    intro = f'''
{Fore.CYAN}Web Testing Framework{Style.RESET_ALL}
Type 'help' or '?' to list commands.
'''
    prompt = f'{Fore.GREEN}pyhunter{Style.RESET_ALL}> '

    def __init__(self):
        super().__init__()
        self.modules: Dict[str, Module] = {}
        self.current_module: Optional[Module] = None
        self.global_options = {
            'target': None,
            'port': '80',
            'ssl': False
        }
        self.module_builder = ModuleBuilder()
        self.initialize_environment()
        self.executor = concurrent.futures.ThreadPoolExecutor()
        self.logs_dir = os.path.expanduser(LOG_DIR)
        os.makedirs(self.logs_dir, exist_ok=True)
        self.current_log_timestamp = None 
        self.is_running = False 
        self.ssh_handler = SSHHandler()
        self.module_status: Dict[str, ModuleStatus] = {}
        self.status_lock = Lock()

        self.reports_dir = os.path.expanduser(REPORT_DIR)
        os.makedirs(self.reports_dir, exist_ok=True)
        self.report_generator = ReportGenerator(self.reports_dir)

        self.session_start = datetime.now()
        self.module_status: Dict[str, ModuleStatus] = {}

    def initialize_environment(self):
        """Initialize the environment and build modules if needed"""
        print(f"{Fore.CYAN}Initializing environment...{Style.RESET_ALL}")
        if self.module_builder.build_all_modules():
            print(f"{Fore.GREEN}All modules built successfully{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}Some modules failed to build{Style.RESET_ALL}")
        self.load_modules()

    def do_rebuild(self, arg: str):
        """Rebuild all modules or a specific module
        Usage: rebuild [module_name]"""
        if arg:
            if arg in self.modules:
                module_path = self.modules[arg].path
                if self.module_builder.build_module(module_path):
                    print(f"{Fore.GREEN}Successfully rebuilt module: {arg}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Failed to rebuild module: {arg}{Style.RESET_ALL}")
        else:
            if self.module_builder.build_all_modules():
                print(f"{Fore.GREEN}Successfully rebuilt all modules{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Some modules failed to rebuild{Style.RESET_ALL}")

    def do_connect(self, arg: str):
        """Connect to remote host via SSH
        Usage: connect <hostname> <username> [--password <pass>] [--key <path>] [--port <port>]"""
        args = arg.split()
        if len(args) < 2:
            print(f"{Fore.RED}Usage: connect <hostname> <username> [--password <pass>] [--key <path>] [--port <port>]{Style.RESET_ALL}")
            return
            
        hostname, username = args[0:2]
        password = None
        key_path = None
        port = 22
        
        # Parse optional arguments
        i = 2
        while i < len(args):
            if args[i] == "--password" and i + 1 < len(args):
                password = args[i + 1]
                i += 2
            elif args[i] == "--key" and i + 1 < len(args):
                key_path = args[i + 1]
                i += 2
            elif args[i] == "--port" and i + 1 < len(args):
                port = int(args[i + 1])
                i += 2
            else:
                i += 1
        
        if self.ssh_handler.connect(hostname, username, password, key_path, port):
            print(f"{Fore.GREEN}Connected to {hostname}{Style.RESET_ALL}")
            self.update_prompt()
    
    def do_disconnect(self, arg: str):
        """Disconnect from remote host"""
        if self.ssh_handler.connection:
            self.ssh_handler.disconnect()
            print(f"{Fore.GREEN}Disconnected from remote host{Style.RESET_ALL}")
            self.update_prompt()
        else:
            print(f"{Fore.YELLOW}Not connected to any remote host{Style.RESET_ALL}")

    def emptyline(self):
        """Do nothing on empty input line"""
        pass

    def load_modules(self):
        """Dynamically load Go modules from the modules directory"""
        modules_dir = os.path.expanduser(MOD_DIR)
        if not os.path.exists(modules_dir):
            os.makedirs(modules_dir)

        loaded_modules_count = 0  # Initialize a counter for loaded modules

        for file_path in Path(modules_dir).glob("*"):
            if file_path.is_file() and os.access(file_path, os.X_OK):
                try:
                    # Execute the Go binary with the `-metadata` flag to get module metadata
                    result = subprocess.run([str(file_path), "-metadata"], capture_output=True, text=True)
                    if result.returncode != 0:
                        print(f"Error retrieving metadata from {file_path.name}: {result.stderr}")
                        continue

                    metadata = json.loads(result.stdout)
                    
                    # Create the module using the metadata
                    parameters = [
                        ModuleParameter(**param) for param in metadata.get("parameters", [])
                    ]
                    mod = Module(
                        name=metadata["name"],
                        description=metadata["description"],
                        author=metadata["author"],
                        parameters=parameters,
                        category=metadata.get("category", "Uncategorized"),
                        path=str(file_path),
                        dependencies=metadata.get("dependencies", []),
                        install_command=metadata.get("install_command", "")
                    )
                    self.modules[mod.name] = mod
                    loaded_modules_count += 1  # Increment the counter

                except Exception as e:
                    print(f"{Fore.RED}Error loading module {file_path}: {e}{Style.RESET_ALL}")

        # Print the total number of loaded modules
        print(f"{Fore.GREEN}Total modules loaded: {loaded_modules_count}{Style.RESET_ALL}")

    def do_install_items(self, module_name: str):
        """Install dependencies for the specified module or all modules"""
        if module_name == "all":
            for mod in self.modules.values():
                self.install_module(mod)
        elif module_name in self.modules:
            self.install_module(self.modules[module_name])
        else:
            print(f"{Fore.RED}Module not found: {module_name}{Style.RESET_ALL}")

    def install_module(self, module: Module):
        """Install a module's dependencies using its install command"""
        if module.install_command:
            print(f"{Fore.CYAN}Installing dependencies for module '{module.name}'...{Style.RESET_ALL}")
            try:
                subprocess.run(module.install_command, shell=True, check=True)
                print(f"{Fore.GREEN}Dependencies for module '{module.name}' installed successfully.{Style.RESET_ALL}")
            except subprocess.CalledProcessError as e:
                print(f"{Fore.RED}Failed to install dependencies: {e}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}No installation command specified for module '{module.name}'.{Style.RESET_ALL}")


    def execute_module_in_background(self):
        """Submit the module execution to the background thread"""
        module_name = self.current_module.name
        
        # Create ModuleStatus with parameters
        current_params = {
            param.name: param.value if param.value is not None else param.default
            for param in self.current_module.parameters
        }
        
        with self.status_lock:
            self.module_status[module_name] = ModuleStatus(
                start_time=datetime.now(),
                is_running=True,
                parameters=current_params
            )
        
        future = self.executor.submit(self.execute_module)
        future.add_done_callback(lambda f: self.log_results(f, module_name))


    def log_results(self, future, module_name: str):
        """Callback to log results after execution"""
        try:
            result = future.result()
            log_file_path = os.path.join(self.logs_dir, f"{module_name}_{self.current_log_timestamp}.log")
            
            with open(log_file_path, "w") as log_file:
                log_file.write(result + "\n")
            print(f"{Fore.GREEN}Execution completed. Results logged to {log_file_path}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error logging results: {e}{Style.RESET_ALL}")
        finally:
            with self.status_lock:
                if module_name in self.module_status:
                    self.module_status[module_name].is_running = False
            self.current_log_timestamp = None


    def do_show_output(self, module_name: str):
        """Display the output of the specified module's log file."""
        log_files = sorted(Path(self.logs_dir).glob(f"{module_name}.log"), reverse=True) 
                
        if log_files:
            # Display the most recent log or list available logs for user selection
            print(f"{Fore.GREEN}Available logs for module '{module_name}':{Style.RESET_ALL}")
            for i, log_file in enumerate(log_files, 1):
                print(f"{i}. {log_file.name}")
            with open(log_files[0], "r") as log_file:
                print(f"\n{Fore.CYAN}Displaying latest log:{Style.RESET_ALL}")
                print(log_file.read())
        else:
            print(f"{Fore.RED}No logs found for module: {module_name}{Style.RESET_ALL}")


    def complete_show_output(self, text, line, begidx, endidx):
        """Tab completion for log files in the logs directory for show_output command."""
        log_files = [f.stem for f in Path(self.logs_dir).glob("*.log")]
        if text:
            return [f for f in log_files if f.startswith(text)]
        else:
            return log_files

    def complete_use(self, text, line, begidx, endidx):
        return [mod for mod in self.modules if mod.startswith(text)]

    def complete_show(self, text, line, begidx, endidx):
        return [cmd for cmd in ['modules', 'options', 'info'] if cmd.startswith(text)]

    def complete_set(self, text, line, begidx, endidx):
        if self.current_module:
            return [param.name for param in self.current_module.parameters if param.name.startswith(text)]
        return list(self.global_options.keys())

    def do_use(self, module_name: str):
        """Select a module to use"""
        if module_name in self.modules:
            self.current_module = self.modules[module_name]
            self.update_prompt()
            print(f"\n{Fore.CYAN}Using module: {self.current_module.name}{Style.RESET_ALL}")

            # Check for dependencies
            self.check_dependencies(self.current_module)
            
            self.do_show("info")
        else:
            print(f"{Fore.RED}Module not found: {module_name}{Style.RESET_ALL}")

    def do_show(self, arg: str):
        """Show modules, module options, or module information"""
        if arg == "modules":
            self.show_modules()
        elif arg == "options":
            if self.current_module:
                self.print_module_info()
            else:
                print(f"{Fore.YELLOW}No module selected. Use 'use <module>' first.{Style.RESET_ALL}")
        elif arg == "info":
            if self.current_module:
                self.print_module_info()
            else:
                print(f"{Fore.YELLOW}No module selected. Use 'use <module>' first.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Invalid argument. Use 'show modules', 'show options', or 'show info'{Style.RESET_ALL}")

    def do_set(self, arg: str):
        """Set a module parameter or global option"""
        try:
            param_name, value = arg.split()
            if self.current_module:
                for param in self.current_module.parameters:
                    if param.name == param_name:
                        param.value = value
                        print(f"{Fore.GREEN}Set {param_name} => {value}{Style.RESET_ALL}")
                        return
                
                # If not found in module parameters, check global options
                if param_name in self.global_options:
                    self.global_options[param_name] = value
                    print(f"{Fore.GREEN}Set global {param_name} => {value}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Parameter not found: {param_name}{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Usage: set <parameter> <value>{Style.RESET_ALL}")

    
    def do_show_status(self, module_name: str):
        """Show the status of a running module
        Usage: show_status <module_name>"""
        if not module_name:
            self.show_all_status()
            return

        if module_name not in self.modules:
            print(f"{Fore.RED}Module not found: {module_name}{Style.RESET_ALL}")
            return

        with self.status_lock:
            status = self.module_status.get(module_name)
            if not status:
                print(f"{Fore.YELLOW}No status information available for module: {module_name}{Style.RESET_ALL}")
                return

            self.print_module_status(module_name, status)

    def show_all_status(self):
        """Show status of all modules that have been run"""
        with self.status_lock:
            if not self.module_status:
                print(f"{Fore.YELLOW}No modules are currently running or have been run{Style.RESET_ALL}")
                return

            print(f"\n{Fore.CYAN}=== Module Status Overview ==={Style.RESET_ALL}")
            for module_name, status in self.module_status.items():
                self.print_module_status(module_name, status)
                print("-" * 50)

    def print_module_status(self, module_name: str, status: ModuleStatus):
        """Print detailed status information for a module"""
        runtime = datetime.now() - status.start_time
        status_color = Fore.GREEN if not status.is_running else Fore.YELLOW
        status_text = "RUNNING" if status.is_running else "COMPLETED"
        
        print(f"\n{Fore.CYAN}Module: {module_name}{Style.RESET_ALL}")
        print(f"Status: {status_color}{status_text}{Style.RESET_ALL}")
        print(f"Start Time: {status.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Runtime: {str(runtime).split('.')[0]}")  # Format without microseconds
        if status.total_tasks > 0:
            progress_pct = (status.progress / status.total_tasks) * 100
            print(f"Progress: {progress_pct:.1f}% ({status.progress}/{status.total_tasks})")
        if status.last_update:
            print(f"Last Update: {status.last_update}")

    def complete_show_status(self, text, line, begidx, endidx):
        """Tab completion for show_status command"""
        if text:
            return [mod for mod in self.modules if mod.startswith(text)]
        return list(self.modules.keys())

    def update_module_status(self, module_name: str, progress: int = None, total_tasks: int = None, last_update: str = None):
        """Update the status of a running module"""
        with self.status_lock:
            if module_name in self.module_status:
                status = self.module_status[module_name]
                if progress is not None:
                    status.progress = progress
                if total_tasks is not None:
                    status.total_tasks = total_tasks
                if last_update is not None:
                    status.last_update = last_update

    def do_run(self, arg: str):
        """Run the current module in the background"""
        if not self.current_module:
            print(f"{Fore.RED}No module selected. Use 'use <module>' first.{Style.RESET_ALL}")
            return

        # if self.is_running:
        #     print(f"{Fore.YELLOW}Module is already running. Please wait until it completes.{Style.RESET_ALL}")
        #     return

        missing_params = [param.name for param in self.current_module.parameters if param.required and not param.value and not param.default]
        if missing_params:
            print(f"{Fore.RED}Missing required parameters: {', '.join(missing_params)}{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}Running module: {self.current_module.name} in background{Style.RESET_ALL}")

        self.current_log_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.is_running = True 
        self.execute_module_in_background()

    def check_dependencies(self, module: Module):
        """Check if the required dependencies are installed"""
        missing_deps = []
        
        for dep in module.dependencies:
            if shutil.which(dep) is None:
                missing_deps.append(dep)

        if missing_deps:
            print(f"{Fore.RED}Missing dependencies for module '{module.name}': {', '.join(missing_deps)}{Style.RESET_ALL}")
            install = input(f"{Fore.YELLOW}Do you want to install missing dependencies? (y/n): {Style.RESET_ALL}")
            if install.lower() == 'y':
                self.install_module(module)
        else:
            print(f"{Fore.GREEN}All dependencies are satisfied for module '{module.name}'.{Style.RESET_ALL}")


    def execute_module(self):
        """Execute the current module using its configuration"""
        try:
            # Build parameters with user-defined values taking precedence
            params = {param.name: (param.value if param.value is not None else param.default) 
                    for param in self.current_module.parameters}

            # Merge global options
            params.update({k: v for k, v in self.global_options.items() 
                        if k not in params or params[k] is None})

            # Get module binary name
            module_name = os.path.splitext(os.path.basename(self.current_module.path))[0]
            binary_name = f"{module_name}"
            if os.name == 'nt':  # Windows
                binary_name += '.exe'

            # Get binary path
            binary_path = os.path.join(os.path.dirname(self.current_module.path), binary_name)

            if self.ssh_handler.connection:
                # For remote execution
                remote_binary = f"/tmp/{binary_name}"
                
                # Upload binary
                self.ssh_handler.upload_file(binary_path, remote_binary)
                self.ssh_handler.execute_command(f"chmod +x {remote_binary}")

                # Execute remotely with parameters
                params_json = json.dumps(params)
                cmd = f"{remote_binary} --params '{params_json}'"
                stdout, stderr = self.ssh_handler.execute_command(cmd)
                
                # Clean up
                self.ssh_handler.execute_command(f"rm {remote_binary}")

                if stderr:
                    return f"{Fore.RED}Error executing module: {stderr}{Style.RESET_ALL}"

                # Parse result
                try:
                    result = json.loads(stdout)
                    if "error" in result:
                        return f"{Fore.RED}Module execution error: {result['error']}{Style.RESET_ALL}"
                    return f"{Fore.CYAN}{self.current_module.name} executed with result: {result['output']}{Style.RESET_ALL}"
                except json.JSONDecodeError:
                    return f"{Fore.RED}Error parsing module output: {stdout}{Style.RESET_ALL}"
            else:
                # Local execution
                params_json = json.dumps(params)
                try:
                    result = subprocess.run(
                        [binary_path, "--params", params_json],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    output = json.loads(result.stdout)
                    if "error" in output:
                        return f"{Fore.RED}Module execution error: {output['error']}{Style.RESET_ALL}"
                    return f"{Fore.CYAN}{self.current_module.name} executed with result: {output['output']}{Style.RESET_ALL}"
                except subprocess.CalledProcessError as e:
                    return f"{Fore.RED}Error executing module: {e.stderr}{Style.RESET_ALL}"

        except Exception as e:
            return f"{Fore.RED}Error executing module: {e}{Style.RESET_ALL}"

    def show_modules(self):
        """Display all available modules"""
        print(f"\n{'Name':<20} {'Category':<15} {'Description':<40}")
        print("-" * 75)
        for name, module in self.modules.items():
            print(f"{Fore.CYAN}{name:<20}{Style.RESET_ALL} "
                  f"{module.category:<15} {module.description:<40}")

    def print_module_info(self):
        """Print detailed information about the current module"""
        if not self.current_module:
            print(f"{Fore.RED}No current module selected.{Style.RESET_ALL}")
            return

        # Header for the module
        print(f"\n{Fore.CYAN}=== Module: {self.current_module.name} ==={Style.RESET_ALL}")
        print(f"{Fore.LIGHTWHITE_EX}  Author: {self.current_module.author}")
        print(f"  Description: {self.current_module.description}")
        print(f"  Category: {self.current_module.category}{Style.RESET_ALL}\n")

        # Parameters header
        print(f"{Fore.GREEN}Parameters:{Style.RESET_ALL}")
        print(f"{'Name':<20} {'Required':<10} {'Default':<15} {'Description':<40} {'Value':<25}")
        print("-" * 100)  # Separator line

        # Iterate over parameters
        for param in self.current_module.parameters:
            value_display = str(param.value) if param.value is not None else "None"
            # Format each row with clearer spacing
            print(f"{Fore.YELLOW}{param.name:<20}{Style.RESET_ALL} "
                f"{'Yes' if param.required else 'No':<10} "
                f"{str(param.default):<15} "
                f"{param.description:<40} "
                f"{value_display:<25}")

        print("\n")

    def do_generate_report(self, arg: str):
        """Generate a report for the current session
        Usage: generate_report [name]
        If name is not provided, timestamp will be used"""
        try:
            # Generate report name
            if not arg:
                report_name = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            else:
                report_name = arg.strip()

            # Generate markdown report
            markdown_content = self.report_generator.generate_markdown(
                self.logs_dir,
                self.module_status
            )
            
            # Save markdown report
            markdown_path = os.path.join(self.reports_dir, f"{report_name}.md")
            with open(markdown_path, 'w') as f:
                f.write(markdown_content)

            # Generate and save HTML report
            html_content = self.report_generator.generate_html(
                markdown_content,
                self.module_status
            )
            html_path = os.path.join(self.reports_dir, f"{report_name}.html")
            with open(html_path, 'w') as f:
                f.write(html_content)

            print(f"{Fore.GREEN}Reports generated successfully:{Style.RESET_ALL}")
            print(f"Markdown report: {markdown_path}")
            print(f"HTML report: {html_path}")

        except Exception as e:
            print(f"{Fore.RED}Error generating report: {str(e)}{Style.RESET_ALL}")

    def main_menu(self):
        """Return to the main menu"""
        self.current_module = None
        self.update_prompt()

    def do_back(self, arg: str):
        """Exit the current module and return to the main prompt"""
        self.main_menu()
        print(f"{Fore.CYAN}Returned to main console{Style.RESET_ALL}")

    def update_prompt(self):
        """Updated to show remote connection status"""
        if self.ssh_handler.connection:
            remote_info = f"@{self.ssh_handler.connection.hostname}"
        else:
            remote_info = ""
            
        if self.current_module:
            self.prompt = f"{Fore.GREEN}pyhunter{remote_info}({self.current_module.name}){Style.RESET_ALL}> "
        else:
            self.prompt = f"{Fore.GREEN}pyhunter{remote_info}{Style.RESET_ALL}> "

    def do_exit(self, arg: str):
        """Exit the application"""
        return True

    def do_quit(self, arg: str):
        """Exit the application"""
        return True


class ModuleDownloader:
    def __init__(self, github_repo: str, local_dir: str):
        self.github_repo = github_repo
        self.local_dir = Path(local_dir)
        self.base_url = f'https://api.github.com/repos/{github_repo}/contents/modules'
        self.hash_file = self.local_dir / '.module_hashes.json'

    def download_modules(self):
        """Download only new or updated .go files from the GitHub modules directory to the local directory."""
        self.local_dir.mkdir(parents=True, exist_ok=True) 

        # Load previous hashes
        previous_hashes = self._load_hashes()
        new_hashes = {}

        # Download modules and get updated hashes
        self._download_from_github(self.base_url, previous_hashes, new_hashes)

        # Save updated hashes
        self._save_hashes(new_hashes)

    def _download_from_github(self, url: str, previous_hashes: dict, new_hashes: dict):
        """Recursively download updated .go files from the specified GitHub URL."""
        response = requests.get(url)
        response.raise_for_status()

        for item in response.json():
            if item['type'] == 'file' and item['name'].endswith('.go'):
                file_sha = item['sha']
                file_path = self.local_dir / item['name']

                # Check if the file is new or has been updated
                if previous_hashes.get(item['name']) != file_sha:
                    self._download_file(item['download_url'], file_path)
                    print(f'Downloaded {item["name"]} to {file_path}')

                # Update new_hashes dictionary
                new_hashes[item['name']] = file_sha

            elif item['type'] == 'dir':
                # Recursively download files from the directory
                sub_dir_url = item['url']
                self._download_from_github(sub_dir_url, previous_hashes, new_hashes)

    def _download_file(self, file_url: str, file_path: Path):
        """Download a single file and save it to the specified path."""
        file_response = requests.get(file_url)
        file_response.raise_for_status()

        with open(file_path, 'wb') as f:
            f.write(file_response.content)

    def _load_hashes(self) -> dict:
        """Load the previous file hashes from the local hash file."""
        if self.hash_file.exists():
            with open(self.hash_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_hashes(self, hashes: dict):
        """Save the current file hashes to the local hash file."""
        with open(self.hash_file, 'w') as f:
            json.dump(hashes, f, indent=4)


def main():
    github_repo = 'mavedirra-01/pyhunter3' 
    home_dir = Path.home() / MOD_DIR

    downloader = ModuleDownloader(github_repo, home_dir)
    downloader.download_modules()

    # Start the main WebTestConsole
    WebTestConsole().cmdloop()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Exiting...{Style.RESET_ALL}")