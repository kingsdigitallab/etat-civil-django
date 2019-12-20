#!/usr/bin/env python

import os

import pandas as pd
from places import get_sheet


def collect_data(data_dir, locations_csv):
    locations_df = pd.read_csv(locations_csv)
    locations_df = locations_df.set_index('location')

    births_df = pd.DataFrame()
    deaths_df = pd.DataFrame()
    marriages_df = pd.DataFrame()

    for fn in sorted(os.listdir(data_dir)):
        if not fn.endswith('.xlsx'):
            continue

        print('.', fn)

        location = fn.split('.')[0]

        fn = os.path.join(data_dir, fn)
        births_df = births_df.append(
            get_couple_df(
                get_sheet(fn, 'Naissances'), 'birth', location, locations_df))
        deaths_df = deaths_df.append(
            get_deaths_df(get_sheet(fn, 'Décès'), location, locations_df))
        marriages_df = marriages_df.append(
            get_couple_df(
                get_sheet(fn, 'Mariages'), 'marriage', location, locations_df))

    births_df.to_csv('../processed/births.tsv', sep='\t', index=False)
    deaths_df.to_csv('../processed/deaths.tsv', sep='\t', index=False)
    marriages_df.to_csv('../processed/marriages.tsv', sep='\t', index=False)


def get_couple_df(in_df, t, location, locations_df):
    persons = ['groom', 'bride']

    df = pd.DataFrame()

    df['deed_number'] = in_df['deed number']
    df['deed_date'] = in_df['deed date']
    df['deed_location'] = get_location(locations_df, location)
    df['{}_date'.format(t)] = ''

    if t == 'birth':
        df['birth_legitimate'] = in_df['legitimate birth'].apply(
            lambda x: 'TRUE' if x == 'Oui' else 'FALSE')
        persons = ['father', 'mother']

    for person in persons:
        df['{}_name'.format(
            person)] = in_df['{}\'s first name'.format(person)].str.strip()
        df['{}_surname'.format(
            person)] = in_df['{}\'s surname'.format(person)].str.strip()
        df['{}_age'.format(person)] = in_df['{}\'s age'.format(person)]
        df['{}_profession'.format(
            person)] = in_df['{}\'s profession'.format(person)].str.strip()
        df['{}_domicile'.format(
            person)] = in_df['{}\'s domicile'.format(person)].apply(
            lambda x: '' if pd.isna(x) else get_location(
                locations_df, str(x).strip())
        )
        df['{}_birth_location'.format(person)] = get_location_data(
            locations_df, in_df, '{}\'s '.format(person), 'birthplace')
        df['{}_previous_domicile_location'.format(person)] = get_location_data(
            locations_df, in_df, '{}\'s '.format(person), 'previous domicile')

    df['comments'] = in_df['comments']
    df['classmark'] = in_df['classmark (etat civil, volumes)']
    df['classmark_microfilm'] = in_df['microfilm classmark']

    return df


def get_location(locations_df, name):
    try:
        return locations_df.loc[name]['display_name']
    except KeyError:
        return name


def get_location_data(locations_df, df, person, location_type):
    return df[
        '{}{} (locality)'.format(person, location_type)
    ].str.strip(
    ).str.cat(
        df[
            '{}{} (region or département)'.format(person, location_type)
        ].str.strip(), sep=', ', na_rep='!!!'
    ).replace(
        to_replace=r'(!!!, !!!)|(!!!, )|(, !!!)', value='', regex=True
    ).apply(
        lambda x: get_location(locations_df, x)
    )


def get_deaths_df(in_df, location, locations_df):
    df = pd.DataFrame()

    df['deed_number'] = in_df['deed number']
    df['deed_date'] = in_df['deed date']
    df['deed_location'] = get_location(locations_df, location)
    df['death_date'] = ''

    df['name'] = in_df['deceased\'s first name'].str.strip()
    df['surname'] = in_df['deceased\'s surname'].str.strip()
    df['gender'] = ''
    df['age'] = in_df['age']
    df['profession'] = in_df['profession'].str.strip()
    df['domicile'] = in_df['domicile'].apply(
        lambda x: '' if pd.isna(x) else get_location(
            locations_df, str(x).strip())
    )
    df['birth_location'] = get_location_data(
        locations_df, in_df, '', 'birthplace')

    df['comments'] = in_df['comments']
    df['classmark'] = in_df['classmark (etat civil, volumes)']
    df['classmark_microfilm'] = in_df['microfilm classmark']

    return df


if __name__ == '__main__':
    collect_data('../raw', '../interim/locations.csv')
