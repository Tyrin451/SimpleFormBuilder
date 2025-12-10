from typing import Dict, Any, Optional

class LaTeXTemplateLibrary:
    """
    Library of predefined LaTeX templates for SimpleFormBuilder.
    Allows defining row formats and environment types for different kinds of steps.
    """

    DEFAULT_TEMPLATES = {
        "standard": {
            "description": "Standard alignment for all steps",
            "environments": {
                "param": "align*",
                "eq": "align*",
                "check": "align*"
            },
            "rows": {
                "param": r"{symbol} &= {value} && \text{{{desc}}} \\",
                "eq": r"{symbol} &= {expr} = {value} && \text{{{desc}}} \\",
                "check": r"\text{{{name}}} : &&& \text{{{desc}}} \\ & {expr} \rightarrow {status} &&  \\"
            }
        },
        "compact": {
            "description": "Compact representation",
            "environments": {
                "param": "align*",
                "eq": "align*",
                "check": "align*"
            },
            "rows": {
                "param": r"{symbol} &= {value} \\",
                "eq": r"{symbol} &= {value} \\",
                "check": r"\text{{{name}}} &: {status} \\"
            }
        },
        "detailed": {
            "description": "Detailed representation with descriptions first",
            "environments": {
                "param": "itemize",
                "eq": "itemize",
                "check": "itemize"
            },
            "rows": {
                "param": r"\item \textbf{{{desc}}}: ${symbol} = {value}$",
                "eq": r"\item \textbf{{{desc}}}: ${symbol} = {expr} = {value}$",
                "check": r"\item \textbf{{{desc}}}: Checking ${expr}$ $\rightarrow$ {status}"
            }
        }
    }

    @classmethod
    def get_template(cls, name_or_dict: Any) -> Dict[str, Any]:
        """
        Retrieves a template by name or returns the dictionary if one is provided.
        Defaults to 'standard' if name is not found.
        """
        if isinstance(name_or_dict, dict):
            return name_or_dict
        
        if isinstance(name_or_dict, str):
            return cls.DEFAULT_TEMPLATES.get(name_or_dict, cls.DEFAULT_TEMPLATES["standard"])
        
        return cls.DEFAULT_TEMPLATES["standard"]
