import pandas as pd
import os
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

projects = os.listdir('resultados')
main_df = pd.DataFrame(columns=[
    'library', '#app_first', '#lang_first', '#third_first', 'total_first',
    '#app_last', '#lang_last', '#third_last', 'total_last'], index=projects)


def calculate_info(project_name, url, version):
    raise_df, reraise_df = load_df(url)
    df = pd.concat([raise_df, reraise_df])
    df = df[~((df['exception_name'] == '**') | (df['origin'] == '**'))]

    user = df[df['origin'] == 'usr']['origin'].count()
    system = df[df['origin'] == 'sys']['origin'].count()
    third = df[df['origin'] == 'lib']['origin'].count()
    total = df['origin'].count()
    count = df['exception_name'].value_counts().reset_index(level=0).rename(columns={'exception_name': 'count', 'index': 'exception_name'})
    
    different_types = count.merge(df[['exception_name', 'origin']], on='exception_name', how='inner').drop_duplicates('exception_name')
    different_types.to_csv('exceptions/{}_{}.csv'.format(project_name, version), index=False)

    return [project_name, user, system, third, total] if version == 'first' else [user, system, third, total]

def load_df(url):
    raise_df = pd.read_csv(os.path.join(url, 'Raise.csv'), sep=';', usecols=['rel_path', 'class_name', 'func_name', 'exception_name', 'origin'])
    reraise_df = pd.read_csv(os.path.join(url, 'Reraise.csv'), sep=';')
    return raise_df, reraise_df

projects = os.listdir('resultados')
for project_name in projects:
    project_url = os.path.join('resultados', project_name)
    versions = sorted(os.listdir(project_url))
    line = []
    
    first_url = os.path.join(project_url, versions[0])
    line.extend(calculate_info(project_name, first_url, 'first'))
    last_url = os.path.join(project_url, versions[-1])
    line.extend(calculate_info(project_name, last_url, 'last'))
    main_df.loc[project_name] = line

main_df.reset_index(drop=True).to_csv('projects_data.csv', sep=';', index=False)