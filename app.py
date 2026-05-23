import math
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ---------- Safe function evaluator ----------
def safe_eval(expr, x):
    allowed_names = {
        'x': x,
        'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
        'exp': math.exp, 'log': math.log, 'sqrt': math.sqrt,
        'pi': math.pi, 'e': math.e, 'abs': math.fabs,
        'pow': math.pow
    }
    try:
        return eval(expr, {"__builtins__": {}}, allowed_names)
    except Exception as e:
        raise ValueError(f"Error evaluating function: {e}")

# ---------- Secant Method ----------
def secant_method(f_str, x0, x1, tol=1e-6, max_iter=50):
    iterations = []
    x_prev = x0
    x_curr = x1
    f_prev = safe_eval(f_str, x_prev)
    f_curr = safe_eval(f_str, x_curr)

    # n=1: Initial pair (x₀, x₁) with first x₂ calculation
    # Compute x₂
    if abs(f_curr - f_prev) < 1e-14:
        raise ValueError("Division by near-zero difference")
    x_new = x_curr - f_curr * (x_curr - x_prev) / (f_curr - f_prev)
    f_new = safe_eval(f_str, x_new)
    error = abs(x_new - x_curr)

    iterations.append({
        'n': 1,
        'x_n': x_prev,      # x₀ = 0
        'f_x_n': f_prev,    # f(x₀) = -4
        'x_n1': x_curr,     # x₁ = 3
        'f_x_n1': f_curr,   # f(x₁) = 5
        'x_next': x_new,    # x₂ = 1.333333
        'f_next': f_new,    # f(x₂) = -2.222222
        'error': error,
        'step': f"x₂ = {x_curr} - ({f_curr})×({x_curr}-{x_prev})/({f_curr}-({f_prev})) = {x_new}"
    })

    if error < tol:
        return iterations, x_new

    # Shift for next iteration
    x_prev = x_curr      # x₁ = 3
    f_prev = f_curr      # f(x₁) = 5
    x_curr = x_new       # x₂ = 1.333333
    f_curr = f_new       # f(x₂) = -2.222222

    for n in range(2, max_iter + 1):
        if abs(f_curr - f_prev) < 1e-14:
            raise ValueError("Division by near-zero difference")

        x_new = x_curr - f_curr * (x_curr - x_prev) / (f_curr - f_prev)
        f_new = safe_eval(f_str, x_new)
        error = abs(x_new - x_curr)

        step_str = (
            f"x{n+1} = {x_curr} - ({f_curr})×({x_curr}-{x_prev})/({f_curr}-({f_prev})) = {x_new}"
        )

        iterations.append({
            'n': n,
            'x_n': x_prev,      # x_{n-1}
            'f_x_n': f_prev,    # f(x_{n-1})
            'x_n1': x_curr,     # x_n
            'f_x_n1': f_curr,   # f(x_n)
            'x_next': x_new,    # x_{n+1}
            'f_next': f_new,    # f(x_{n+1})
            'error': error,
            'step': step_str
        })

        if error < tol:
            return iterations, x_new

        x_prev = x_curr
        f_prev = f_curr
        x_curr = x_new
        f_curr = f_new

    raise ValueError(f"Method did not converge within {max_iter} iterations.")

# ---------- Routes ----------
@app.route('/')
def index():
    return render_template('secant.html')

@app.route('/calculate/secant', methods=['POST'])
def calculate_secant():
    data = request.json
    f_expr = data.get('function', '').strip()
    
    try:
        x0 = float(data.get('x0'))
        x1 = float(data.get('x1'))
        tol = float(data.get('tol', 1e-6))
        max_iter = int(data.get('max_iter', 50))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid numeric inputs.'}), 400

    # Validate inputs
    if x0 == x1:
        return jsonify({'error': 'x₀ and x₁ must be different values.'}), 400
    if tol <= 0:
        return jsonify({'error': 'Tolerance must be positive.'}), 400
    if max_iter < 1:
        return jsonify({'error': 'Max iterations must be at least 1.'}), 400

    try:
        iterations, root = secant_method(f_expr, x0, x1, tol, max_iter)
        
        # Round numbers for clean display
        for it in iterations:
            for key in ['x_n', 'f_x_n', 'x_n1', 'f_x_n1', 'error']:
                if it[key] is not None:
                    it[key] = round(it[key], 10)
        
        return jsonify({
            'root': round(root, 10),
            'iterations': iterations,
            'converged': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)