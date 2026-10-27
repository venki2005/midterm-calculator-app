"""Interactive CLI REPL with dynamic command registration and Colorama."""
import sys
from colorama import init, Fore, Style
from app.calculator import Calculator
from app.calculator_config import CalculatorConfig as Config
from app.exceptions import CalculatorError
from app.input_validators import validate_operands
from app.operations import OperationFactory

init(autoreset=True)

class CommandRegistry:
    commands = {}

    @classmethod
    def register(cls, name: str, description: str):
        def decorator(func):
            cls.commands[name] = {"func": func, "description": description}
            return func
        return decorator

class CalculatorREPL:
    def __init__(self):
        Config.ensure_directories()
        self.calc = Calculator()

    def display_help(self):
        print(f"\n{Fore.CYAN}--- Available Operations ---{Style.RESET_ALL}")
        for op in OperationFactory.list_operations():
            print(f"  {Fore.YELLOW}{op:<12}{Style.RESET_ALL} <num1> <num2>")
        print(f"\n{Fore.CYAN}--- Control Commands ---{Style.RESET_ALL}")
        for cmd, info in CommandRegistry.commands.items():
            print(f"  {Fore.GREEN}{cmd:<12}{Style.RESET_ALL} {info['description']}")
        print()

    def run(self):
        print(f"{Fore.GREEN}=== Enhanced Calculator CLI (Type 'help' for commands, 'exit' to quit) ==={Style.RESET_ALL}")
        while True:
            try:
                raw_input = input(f"{Fore.BLUE}calc > {Style.RESET_ALL}").strip()
                if not raw_input:
                    continue
                parts = raw_input.split()
                cmd = parts[0].lower()

                if cmd == "exit":
                    print(f"{Fore.GREEN}Goodbye!{Style.RESET_ALL}")
                    break
                elif cmd == "help":
                    self.display_help()
                elif cmd in CommandRegistry.commands:
                    CommandRegistry.commands[cmd]["func"](self)
                elif cmd in OperationFactory.list_operations():
                    if len(parts) != 3:
                        print(f"{Fore.RED}Error: Operation requires exactly 2 numerical arguments.{Style.RESET_ALL}")
                        continue
                    a, b = validate_operands(parts[1], parts[2])
                    op_instance = OperationFactory.create_operation(cmd)
                    self.calc.set_operation(op_instance)
                    result = self.calc.perform_operation(a, b)
                    print(f"{Fore.GREEN}Result: {result}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Unknown command: '{cmd}'. Type 'help' to list commands.{Style.RESET_ALL}")
            except CalculatorError as err:
                print(f"{Fore.RED}Error: {err}{Style.RESET_ALL}")
            except (KeyboardInterrupt, EOFError):
                print(f"\n{Fore.GREEN}Exiting calculator.{Style.RESET_ALL}")
                break

@CommandRegistry.register("history", "Display calculation history")
def cmd_history(repl: CalculatorREPL):
    hist = repl.calc.show_history()
    if not hist:
        print(f"{Fore.YELLOW}No history entries available.{Style.RESET_ALL}")
        return
    for idx, c in enumerate(hist, start=1):
        print(f"{Fore.WHITE}{idx}. {c}{Style.RESET_ALL}")

@CommandRegistry.register("clear", "Clear calculation history")
def cmd_clear(repl: CalculatorREPL):
    repl.calc.clear_history()
    print(f"{Fore.YELLOW}Calculation history cleared.{Style.RESET_ALL}")

@CommandRegistry.register("undo", "Undo the last calculation")
def cmd_undo(repl: CalculatorREPL):
    if repl.calc.undo():
        print(f"{Fore.YELLOW}Undo performed.{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}Nothing to undo.{Style.RESET_ALL}")

@CommandRegistry.register("redo", "Redo the undone calculation")
def cmd_redo(repl: CalculatorREPL):
    if repl.calc.redo():
        print(f"{Fore.YELLOW}Redo performed.{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}Nothing to redo.{Style.RESET_ALL}")

@CommandRegistry.register("save", "Save history to CSV")
def cmd_save(repl: CalculatorREPL):
    repl.calc.save_history()
    print(f"{Fore.GREEN}History successfully saved.{Style.RESET_ALL}")

@CommandRegistry.register("load", "Load history from CSV")
def cmd_load(repl: CalculatorREPL):
    repl.calc.load_history()
    print(f"{Fore.GREEN}History successfully loaded.{Style.RESET_ALL}")

if __name__ == "__main__":
    CalculatorREPL().run()