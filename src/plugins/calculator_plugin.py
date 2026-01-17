import re
import math
from decimal import Decimal, InvalidOperation

class Plugin:
    metadata = {
        "name": "Calculator Plugin",
        "version": "2.0",
        "description": "Performs advanced arithmetic calculations with support for basic operations, exponentiation, and trigonometric functions."
    }

    def __init__(self, bot):
        self.bot = bot
        # Define supported operations
        self.operators = {
            '+': lambda x, y: x + y,
            '-': lambda x, y: x - y,
            '*': lambda x, y: x * y,
            '/': lambda x, y: x / y if y != 0 else None,
            '^': lambda x, y: x ** y,
        }
        # Define supported functions
        self.functions = {
            'sin': lambda x: math.sin(math.radians(x)),
            'cos': lambda x: math.cos(math.radians(x)),
            'tan': lambda x: math.tan(math.radians(x)),
            'sqrt': math.sqrt,
            'abs': abs,
        }

    def tokenize(self, expression):
        """Convert expression into tokens"""
        # Replace multiple spaces with single space and trim
        expression = re.sub(r'\s+', ' ', expression.strip())
        
        # Tokenize numbers, operators, functions, and parentheses
        token_pattern = r'(\d*\.?\d+|\w+|[+\-*/^()]|\s)'
        tokens = [t for t in re.findall(token_pattern, expression) if t.strip()]
        return tokens

    def apply_operator(self, operators, values):
        """Apply an operator to values from the stack"""
        if not operators or len(values) < 2:
            return False
        op = operators.pop()
        b = values.pop()
        a = values.pop()
        result = self.operators[op](a, b)
        if result is None:
            return False
        values.append(result)
        return True

    def apply_function(self, func_name, values):
        """Apply a function to a value from the stack"""
        if not values or func_name not in self.functions:
            return False
        value = values.pop()
        try:
            result = self.functions[func_name](value)
            values.append(result)
            return True
        except (ValueError, TypeError):
            return False

    def get_precedence(self, op):
        """Get operator precedence"""
        precedences = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}
        return precedences.get(op, 0)

    def evaluate(self, tokens):
        """Evaluate a list of tokens using Shunting Yard algorithm"""
        values = []
        operators = []
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            if token in self.functions:
                # Handle function calls (e.g., sin, cos)
                if i + 1 < len(tokens) and tokens[i + 1] == '(':
                    # Find matching closing parenthesis
                    paren_count = 1
                    j = i + 2
                    while j < len(tokens) and paren_count > 0:
                        if tokens[j] == '(':
                            paren_count += 1
                        elif tokens[j] == ')':
                            paren_count -= 1
                        j += 1
                    if paren_count == 0:
                        # Evaluate expression inside parentheses
                        sub_result = self.evaluate(tokens[i + 2:j - 1])
                        if sub_result is None:
                            return None
                        values.append(sub_result)
                        if not self.apply_function(token, values):
                            return None
                        i = j
                    else:
                        return None
                else:
                    return None
            elif re.match(r'^-?\d*\.?\d+$', token):
                # Handle numbers
                try:
                    values.append(Decimal(token))
                except InvalidOperation:
                    return None
            elif token in self.operators:
                # Handle operators with precedence
                while (operators and operators[-1] != '(' and 
                       self.get_precedence(operators[-1]) >= self.get_precedence(token)):
                    if not self.apply_operator(operators, values):
                        return None
                operators.append(token)
            elif token == '(':
                operators.append(token)
            elif token == ')':
                while operators and operators[-1] != '(':
                    if not self.apply_operator(operators, values):
                        return None
                if operators and operators[-1] == '(':
                    operators.pop()
                else:
                    return None
            else:
                return None
            i += 1

        # Process remaining operators
        while operators:
            if operators[-1] == '(':
                return None
            if not self.apply_operator(operators, values):
                return None

        return values[0] if values else None

    def process(self, user_input, default_response):
        """Process user input for calculation requests"""
        # Look for "calculate [expression]" or "[expression] = ?"
        match = re.search(r"^(?:calculate\s+(.+)|(.+)\s*=\s*\?$)", user_input.lower().strip())
        if not match:
            return None

        # Get the expression from either capture group
        expression = match.group(1) or match.group(2)
        if not expression:
            return "Please provide a valid mathematical expression."

        try:
            tokens = self.tokenize(expression)
            result = self.evaluate(tokens)
            if result is None:
                return f"Sorry, I couldn't calculate '{expression}'. Please check your expression."
            # Format result to avoid excessive decimal places
            result = round(float(result), 8)
            # Remove trailing .0 for integers
            result_str = str(result).rstrip('0').rstrip('.')
            return f"The result of {expression} is {result_str}."
        except Exception as e:
            return f"Sorry, I couldn't calculate '{expression}'. Error: {str(e)}"

    def on_load(self):
        """Called when plugin is loaded"""
        self.bot.command_registry.register(
            "calc_help",
            lambda bot, args: (
                "Calculator Plugin Commands:\n"
                "calculate [expression] or [expression] = ? : Evaluate a mathematical expression\n"
                "Supported operations: +, -, *, /, ^ (power)\n"
                "Supported functions: sin, cos, tan, sqrt, abs\n"
                "Example: calculate 2 + 3 * sin(30) or 2 + 3 * sin(30) = ?"
            ),
            "Show calculator plugin help"
        )

    def on_unload(self):
        """Called when plugin is unloaded"""
        pass