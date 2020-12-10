# -*- coding: utf-8 -*-
"""
Created on Tue Dec  8 20:11:23 2020

@author: Kremena Yordanova
"""


import dash
import dash_html_components as html
import dash_core_components as dcc
import dash_table as dt
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import dash_table
import numpy as np


stylesheet = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=stylesheet)
server = app.server

text = ''' This dashboard uses 943 recipeis from allrecipes.com. This ....
Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus scelerisque efficitur magna, id sagittis augue egestas vel. Vivamus consectetur turpis nec ornare lacinia. Pellentesque sed convallis erat. Aliquam ut est nisl. Etiam pretium fermentum diam, eu consectetur elit gravida vel.
'''

text_filters = '''You can use these filters to select recipes to load in the table below.
If there are not any recipes matching your filters an error message will be printet on 
the left hand-side indicating that there are any matching results.'''

file = 'https://raw.githubusercontent.com/kremenayo/cooking-recipe-dashboard/main/recipes.csv'
df = pd.read_csv(file, index_col=0)
df = df.sort_values(by='reviews', ascending=False)

# format links
def f(row):
    l = "[{0}]({0})".format(row["url"])
    return l
df["link"] = df.apply(f, axis=1)


# dropdown categories
categories = df['category_main'].unique().tolist()

PAGE_SIZE = 10

app.layout = html.Div([
    html.H1('Cooking Recipe Dashboard', style={'textAlign': 'left'}),
    html.Blockquote('MA 705 Course Project by Kremena Ivanov', style={'textAlign': 'left'}),
    html.B('What is this dashboard about?'),
    html.Section(text, style={'textAlign': 'left'}),
    html.B('How to use this dashboard?'),
    html.Section(text, style={'textAlign': 'left'}),
    html.Br(),
    html.Hr(),
    html.Div([html.Div(text_filters),
              html.Br(),
              
              html.Label("Select category to display: "),
              dcc.Dropdown(id='filter_dropdown',
                           placeholder='Select category...',
                           options=[{'label':c, 'value':c} for c in categories],
                           value='Dessert Recipes'),
              html.Br(),
              html.Label("Select total time (in minutes): "),
              dcc.Input(placeholder='Enter time in minutes...',
                                   id='ttl_time', type='number', value=20),
              html.Br(),
              html.Br(),
              html.Label("Select maximum calories: "),
              dcc.Input(placeholder='Enter max calories...',
                                   id='cals', type='number', value=500)],
             style={'width': '39%', 'display': 'inline-block', 'vertical-align' : 'top'}
             ),
    html.Div([],
             style={'width': '14%', 'display': 'inline-block'}),
    html.Div([dcc.Graph(id='fig_pie')],
             style={'width': '45%', 'display': 'inline-block', 'vertical-align' : 'top'}),
    html.H3('Selected Recipes', style={'textAlign': 'left'}), 
    html.Br(),
    html.Div(className="row",
             children=[
                 html.Div(dash_table.DataTable(id='table-paging-with-graph',
                                               columns=[dict(name='Recipe name', id='name', type='text'),
                                                        dict(name='Sub-category', id='category_sub', type='text'),
                                                        dict(name='# Servings', id='servings', type='text'),
                                                        dict(name='Yield', id='yield', type='text'),
                                                        dict(name='# Reviews', id='reviews', type='text'),
                                                        dict(name='Avg. rating (0-5)', id='stars', type='text'),
                                                        dict(name='Prep time', id='prep_time_min', type='text'),
                                                        dict(name='Cook time', id='cook_time_min', type='text'),
                                                        dict(name='Total time', id='ttl_time_min', type='text'),
                                                        dict(name='Link', id='link', type='text', presentation='markdown')
                                                        ],
                                               page_current=0,
                                               page_size=PAGE_SIZE,
                                               page_action='custom',
                                               filter_action='custom',
                                               filter_query='',
                                               sort_action='custom',
                                               sort_mode='multi',
                                               sort_by=[]
                                               ),
                          style={'width': '99%', 'display': 'inline-block', 'overflowY': 'scroll'}
                          )

                 ]),
    html.Hr(),
    html.B('References:'),
    html.Li(html.A('https://www.allrecipes.com/')),
    html.Li(html.A('https://dash.plotly.com/datatable/callbacks')),
    html.Li(html.A('https://plotly.com/python/pie-charts/')),
    html.Li(html.A('https://github.com/plotly/dash-table/issues/222')),
    html.Br(),
    html.Footer('This project was created ...'),
])


operators = [['ge ', '>='],
             ['le ', '<='],
             ['lt ', '<'],
             ['gt ', '>'],
             ['ne ', '!='],
             ['eq ', '='],
             ['contains '],
             ['datestartswith ']]

def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3



@app.callback(
    Output('table-paging-with-graph', 'data'),
    Input('table-paging-with-graph', "page_current"),
    Input('table-paging-with-graph', "page_size"),
    Input('table-paging-with-graph', "sort_by"),
    Input('table-paging-with-graph', "filter_query"),
    Input('filter_dropdown', 'value'),
    Input('ttl_time', 'value'),
    Input('cals', 'value'))



def update_table(page_current, page_size, sort_by, filter, category, time, cals):
    filtering_expressions = filter.split(' && ')
    dff = df[(df['category_main']==category) & (df['ttl_time_min'] <= time) & (df['calories'] <= cals)]
    for filter_part in filtering_expressions:
        col_name, operator, filter_value = split_filter_part(filter_part)

        if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
            # these operators match pandas series operator method names
            dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
        elif operator == 'contains':
            dff = dff.loc[dff[col_name].str.contains(filter_value)]
        elif operator == 'datestartswith':
            # this is a simplification of the front-end filtering logic,
            # only works with complete fields in standard format
            dff = dff.loc[dff[col_name].str.startswith(filter_value)]

    if len(sort_by):
        dff = dff.sort_values(
            [col['column_id'] for col in sort_by],
            ascending=[
                col['direction'] == 'asc'
                for col in sort_by
            ],
            inplace=False
        )

    return dff.iloc[
            page_current*page_size: (page_current + 1)*page_size
    ].to_dict('records')


@app.callback(
    Output(component_id='fig_pie', component_property='figure'),
    Input('filter_dropdown', 'value'),
    Input('ttl_time', 'value'),
    Input('cals', 'value'))

def update_graph(category, time, cals):
    # category = 'Dessert Recipes'
    # time = 1
    # cals = 400
    
    dff = df[(df['category_main']==category) & (df['ttl_time_min'] <= time) & (df['calories'] <= cals)]
    dff_crosstab = dff.groupby('category_sub')
    dff_crosstab = dff_crosstab['category_sub'].count()
    dff_crosstab = dff_crosstab.to_frame()
    dff_crosstab.columns = ['recipes']
    if dff_crosstab.empty:
        data = pd.DataFrame(index=['No recipes to show'])
        data['recipes'] = 0
        fig = px.pie(data, values=data['recipes'], names=data.index, title='No recipes to show. Please choose different parameters')
    else:
        fig = px.pie(dff_crosstab, values=dff_crosstab['recipes'], names=dff_crosstab.index, title='Recipe sub-categories')
    # fig = px.bar(k, y='recipes', x=k.index, text='recipes')
    # fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
    # fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')


    return fig



if __name__ == '__main__':
    app.run_server(debug=True)
    