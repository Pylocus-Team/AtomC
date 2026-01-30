/**
 * RYNX 2.0 - AST NODE DEFINITIONS (JS RUNTIME)
 * This file is a mirror of ast_nodes.py.
 * Any divergence between PY and JS nodes will trigger a System Panic.
 */

class RynxNode {
    constructor(line, column) {
        this.line = line;
        this.column = column;
        this.type = this.constructor.name;
    }
}

// --- ROOT NODES ---

class Program extends RynxNode {
    constructor(line, column, tasks, startBlock) {
        super(line, column);
        this.tasks = tasks; // Array<TaskDecl>
        this.startBlock = startBlock; // StartNode
    }
}

class StartNode extends RynxNode {
    constructor(line, column, statements, exitStatement) {
        super(line, column);
        this.statements = statements; // Array<Statement>
        this.exitStatement = exitStatement; // EndNode
    }
}

// --- STATEMENTS ---

class VariableDecl extends RynxNode {
    constructor(line, column, name, varType, expression, isLet, isGuess) {
        super(line, column);
        this.name = name;
        this.varType = varType;
        this.expression = expression;
        this.isLet = isLet;
        this.isGuess = isGuess;
    }
}

class TaskDecl extends RynxNode {
    constructor(line, column, name, params, returnType, body) {
        super(line, column);
        this.name = name;
        this.params = params; // [{name: string, type: string}]
        this.returnType = returnType;
        this.body = body; // BlockNode
    }
}

class BlockNode extends RynxNode {
    constructor(line, column, statements) {
        super(line, column);
        this.statements = statements;
    }
}

class EndNode extends RynxNode {
    constructor(line, column, code) {
        super(line, column);
        this.code = code; // 0 or 1
    }
}

// --- EXPRESSIONS ---

class BinaryExpr extends RynxNode {
    constructor(line, column, left, operator, right) {
        super(line, column);
        this.left = left;
        this.operator = operator;
        this.right = right;
    }
}

class Literal extends RynxNode {
    constructor(line, column, value, kind) {
        super(line, column);
        this.value = value;
        this.kind = kind; // 'num', 'dec', 'text', 'yes'
    }
}

class Identifier extends RynxNode {
    constructor(line, column, name) {
        super(line, column);
        this.name = name;
    }
}

class TaskCall extends RynxNode {
    constructor(line, column, taskName, args) {
        super(line, column);
        this.taskName = taskName;
        this.args = args;
    }
}

// --- EXPORT FOR RUNTIME BRIDGE ---
if (typeof module !== 'undefined') {
    module.exports = {
        Program, StartNode, VariableDecl, TaskDecl,
        BlockNode, EndNode, BinaryExpr, Literal,
        Identifier, TaskCall
    };
}