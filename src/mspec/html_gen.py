#!/usr/bin/env python3
import mspec

def render_html():
    dist_dir = mspec.dist_dir / 'html'
    print(f'html: {dist_dir}')


def html_create_page():
    """
    <html>
        <head>
            <title>create</title>
        </head>
        <body>
            <form action="create" method="post">
                <input type="text" name="name" value="name">
                <input type="text" name="value" value="value">
                <input type="submit" value="create">
            </form>
        </body>
    </html>
    """

def html_list_page():
    """
    <html>
        <head>
            <title>list</title>
        </head>
        <body>
            <table>
                <tr>
                    <th>name</th>
                    <th>value</th>
                </tr>
                <tr>
                    <td>name</td>
                    <td>value</td>
                </tr>
            </table>
        </body>
    </html>
    """

def html_read_page():
    pass
