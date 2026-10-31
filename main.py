"""Interactive CLI REPL with dynamic command registration and Colorama."""
import sys
from colorama import init, Fore, Style

from app.calculator import Calculator
from app.calculator_config import CalculatorConfig as Config
from app.exceptions import CalculatorError, OperationError, ValidationError
from app.input_validators import validate_operands
from app.logger import logger
from app.operations import OperationFactory

init(autoreset=True)


class CommandRegistry:
    """Registry using decorator pattern to register commands dynamically."""
    commands = {}

    @classmethod
    def register(cls, name: str, description: str):
        def decorator(func):
            cls.commands[name] = {"func": func, "description": description}
            return func
        return decorator


class CalculatorREPL:
    """Read-Eval-Print Loop interface for the Enhanced Calculator."""

    def __init__(self):
        Config.ensure_directories()
        self.calc = Calculator()

    def display_help(self):
        """Display dynamically generated help menu."""
        print(f"\n{Fore.CYAN}--- Available Operations ---{Style.RESET_ALL}")
        for op in OperationFactory.list_operations():
            print(f"  {Fore.YELLOW}{op:<14}{Style.RESET_ALL} <num1> <num2>")
        print(f"\n{Fore.CYAN}--- Control Commands ---{Style.RESET_ALL}")
        for cmd, info in CommandRegistry.commands.items():
            print(f"  {Fore.GREEN}{cmd:<14}{Style.RESET_ALL} {info['description']}")
        print()

    def run(self):
        """Execute the interactive calculator REPL shell."""
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
                        logger.warning("VALIDATION ERROR: Operation '%s' requires 2 arguments (Received: %d)", cmd, len(parts) - 1)
                        print(f"{Fore.RED}Error: Operation requires exactly 2 numerical arguments.{Style.RESET_ALL}")
                        continue

                    # Parsing / Validation
                    a, b = validate_operands(parts[1], parts[2])
                    
                    # Execution
                    op_instance = OperationFactory.create_operation(cmd)
                    self.calc.set_operation(op_instance)
                    result = self.calc.perform_operation(a, b)
                    print(f"{Fore.GREEN}Result: {result}{Style.RESET_ALL}")
                else:
                    logger.warning("UNKNOWN COMMAND: User entered '%s'", cmd)
                    print(f"{Fore.RED}Unknown command: '{cmd}'. Type 'help' to list commands.{Style.RESET_ALL}")

            except ValidationError as err:
                logger.warning("VALIDATION ERROR: %s (Raw input: '%s')", err, raw_input)
                print(f"{Fore.RED}Validation Error: {err}{Style.RESET_ALL}")

            except OperationError as err:
                logger.error("OPERATION ERROR: Failed executing '%s' - %s", cmd, err)
                print(f"{Fore.RED}Operation Error: {err}{Style.RESET_ALL}")

            except CalculatorError as err:
                logger.error("CALCULATOR DOMAIN ERROR: %s", err)
                print(f"{Fore.RED}Error: {err}{Style.RESET_ALL}")

            except (KeyboardInterrupt, EOFError):
                print(f"\n{Fore.GREEN}Exiting calculator.{Style.RESET_ALL}")
                break

            except Exception as err:
                logger.exception("UNEXPECTED ERROR: An unhandled exception occurred: %s", err)
                print(f"{Fore.RED}Unexpected Error: {err}{Style.RESET_ALL}")


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