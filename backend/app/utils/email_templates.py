from app.config.settings import get_settings

def get_email_html(title: str, content: str, image_url: str | None = None) -> str:
    settings = get_settings()
    
    # Premium design matching the Findora frontend
    # Colors:
    # Primary: #6366f1 (Indigo 500)
    # Background: #f8fafc (Slate 50)
    # Text: #1e293b (Slate 800)
    # Muted: #64748b (Slate 500)
    
    image_section = ""
    if image_url:
        image_section = f"""
            <div style="margin-top: 24px; margin-bottom: 24px; text-align: center;">
                <img src="{image_url}" alt="Item Image" style="max-width: 100%; height: auto; border-radius: 12px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);">
            </div>
        """

    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #1e293b;
            margin: 0;
            padding: 0;
            background-color: #f8fafc;
        }}
        .wrapper {{
            width: 100%;
            background-color: #f8fafc;
            padding: 40px 0;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        .header {{
            text-align: center;
            padding-bottom: 32px;
        }}
        .logo {{
            font-size: 24px;
            font-weight: 800;
            color: #6366f1;
            text-decoration: none;
            letter-spacing: -0.025em;
            display: inline-block;
        }}
        .logo span {{
            background: linear-gradient(to right, #6366f1, #a855f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .card {{
            background-color: #ffffff;
            padding: 40px;
            border-radius: 24px;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            border: 1px solid rgba(226, 232, 240, 0.8);
        }}
        .footer {{
            text-align: center;
            padding-top: 32px;
            font-size: 13px;
            color: #94a3b8;
        }}
        .footer a {{
            color: #6366f1;
            text-decoration: none;
            font-weight: 500;
        }}
        .footer a:hover {{
            text-decoration: underline;
        }}
        h2 {{
            font-size: 20px;
            font-weight: 700;
            margin-top: 0;
            margin-bottom: 24px;
            color: #0f172a;
            text-align: center;
        }}
        h3 {{
            font-size: 16px;
            font-weight: 600;
            margin-top: 28px;
            margin-bottom: 12px;
            color: #334155;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-size: 12px;
        }}
        p {{
            margin-top: 0;
            margin-bottom: 16px;
            color: #475569;
        }}
        strong {{
            color: #0f172a;
            font-weight: 600;
        }}
        ul {{
            padding-left: 0;
            list-style-type: none;
            margin-bottom: 24px;
            background-color: #f1f5f9;
            border-radius: 12px;
            padding: 16px;
        }}
        li {{
            margin-bottom: 8px;
            padding-left: 0;
        }}
        li:last-child {{
            margin-bottom: 0;
        }}
        .btn {{
            display: inline-block;
            background-color: #6366f1;
            color: #ffffff;
            padding: 12px 24px;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            margin-top: 24px;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.4);
        }}
        .btn:hover {{
            background-color: #4f46e5;
        }}
        /* Mobile adjustments */
        @media only screen and (max-width: 600px) {{
            .card {{
                padding: 24px;
                border-radius: 16px;
            }}
            .wrapper {{
                padding: 20px 0;
            }}
        }}
    </style>
</head>
<body>
    <div class="wrapper">
        <div class="container">
            <div class="header">
                <a href="{settings.frontend_base_url}" class="logo">
                    <span>{settings.project_name}</span>
                </a>
            </div>
            
            <div class="card">
                <h2>{title}</h2>
                
                {content}
                
                {image_section}
                
                <div style="text-align: center; margin-top: 32px;">
                    <a href="{settings.frontend_base_url}/dashboard" class="btn">Go to Dashboard</a>
                </div>
            </div>
            
            <div class="footer">
                <p>&copy; {settings.admin_office_name}. All rights reserved.</p>
                <p>
                    <a href="{settings.frontend_base_url}">Help Center</a> &bull; <a href="{settings.frontend_base_url}">Privacy Policy</a>
                </p>
            </div>
        </div>
    </div>
</body>
</html>
"""
