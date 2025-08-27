import argparse
import datetime

import pandas as pd
import plotly.express as px
import plotly.figure_factory as ff
import plotly.io as pio


def main():
    parser = argparse.ArgumentParser(
        prog="Git stat analyser",
        description="Analyse a repo csv and output stats about an author",
    )
    parser.add_argument("--csv", help="CSV with stats to load")
    parser.add_argument("--author", help="Author to analyse")
    parser.add_argument("--save-plots", help="Save plots to disk", action="store_true")
    parser.add_argument(
        "--plot-prefix",
        help="Prefix for plot filenames, default will be author name and time",
    )
    parser.add_argument(
        "--verbose",
        help="Verbose output, prints intermidiate steps",
        action="store_true",
    )
    args = parser.parse_args()
    columns_to_keep = [
        "author",
        "date",
        "message",
        "stats_insertions",
        "stats_deletions",
        "stats_lines",
        "hour",
        "minute",
        "day",
        "message_length",
        "neg",
        "neu",
        "pos",
        "compound",
    ]
    commits_df = pd.read_csv(args.csv, lineterminator="\n")[columns_to_keep]
    author_commits = commits_df[commits_df["author"] == args.author]
    if author_commits.empty:
        print(f"No commits found for {args.author}")
        print("Available authors:")
        for author in commits_df["author"].unique():
            print(f"\t{author}")
        return
    commits_df["is_author"] = commits_df["author"] == args.author
    if args.plot_prefix is None:
        args.plot_prefix = f'{args.author}_{datetime.datetime.now().strftime("%Y%m%d")}'
    ## Default images settings
    # pio.kaleido.scope.default_width = 1920
    # pio.kaleido.scope.default_height = 1080

    # Lets find some fun stats
    stats = []
    # Group by number of rows per user and sort ascending
    authors_ranked_by_commits = (
        commits_df.groupby("author")["message"].count().sort_values(ascending=False)
    )
    if args.verbose:
        print_dataframe(authors_ranked_by_commits, "Authors ranked by commits")
    author_rank = authors_ranked_by_commits.index.get_loc(args.author) + 1
    stats.append(f"Author {args.author} is ranked {author_rank} in number of commits")

    commits_totals = commits_df.groupby("author").sum()
    commits_totals["insertion_deletion_ratio"] = (
        commits_totals["stats_insertions"] / commits_totals["stats_deletions"]
    )
    commits_totals["insertion_deletion_ratio"] = commits_totals[
        "insertion_deletion_ratio"
    ].replace([float("inf")], 0)
    if args.verbose:
        print_dataframe(commits_totals, "Authors ranked by totals")
    totals_columns = [
        "message_length",
        "stats_insertions",
        "stats_deletions",
        "stats_lines",
        "insertion_deletion_ratio",
    ]
    for column in totals_columns:
        author_rank, author_value = get_rank_and_value(
            args.author, commits_totals, column, ascending=False
        )
        stats.append(
            f"Author {args.author} is ranked {author_rank} in totals for {column} with a value of {author_value:.2f}"
        )

    commits_mean = commits_df.groupby("author").mean()
    if args.verbose:
        print_dataframe(commits_mean, "Authors ranked by means")
    means_columns = [
        "message_length",
        "stats_insertions",
        "stats_deletions",
        "stats_lines",
        "neg",
        "neu",
        "pos",
        "compound",
    ]
    for column in means_columns:
        author_rank, author_value = get_rank_and_value(
            args.author, commits_mean, column, ascending=False
        )
        stats.append(
            f"Author {args.author} is ranked {author_rank} in means for {column} with a value of {author_value:.2f}"
        )

    # Print all found stats
    for stat in stats:
        print(stat)

    # Plot some graphs
    # The mean of all message lengths with an arrow pointing to the author
    # author_mean_commit_length = commits_mean['message_length'][args.author]
    # commits_mean['fake_y_plot'] = 0
    # means_message_length_plot = px.scatter(
    #     commits_mean,
    #     x='message_length',
    #     y='fake_y_plot',
    #     title='Mean commit message length'
    # )
    # means_message_length_plot.update_traces(
    #     marker=dict(
    #         size=12,
    #         line=dict(
    #             width=30,
    #             color='DarkSlateGrey'
    #         )
    #     ),
    #     selector=dict(mode='markers')
    # )
    # means_message_length_plot.update_xaxes(
    #     tickangle = 45,
    #     title_text = "Message length",
    #     title_font = {"size": 40, 'color':'white'},
    #     title_standoff = 25,
    #     tickfont=dict(color='white', size=40)
    # )
    # means_message_length_plot.update_layout({
    # 'plot_bgcolor': 'rgba(0, 0, 0, 0)',
    # 'paper_bgcolor': 'rgba(0, 0, 0, 0)',
    # 'yaxis':{'visible':False}
    # })
    # means_message_length_plot.add_annotation(
    #     x=author_mean_commit_length,
    #     y=0,
    #     text=args.author,
    #     showarrow=True,
    #     ay=-300,
    #     font=dict(
    #         family="Gilroy Light, Courier New, monospace",
    #         size=60,
    #         color="#ffffff"
    #     ),
    #     arrowhead=2,
    #     arrowwidth=2,
    #     arrowsize=5,
    #     arrowcolor="#ffffff",
    # )
    # if args.save_plots:
    #     means_message_length_plot.write_image(f'{args.plot_prefix}_message_length.png')

    # Show histogram by the hour comparing author to everyone else
    hour_distplot = ff.create_distplot(
        [
            commits_df[commits_df["is_author"]]["hour"],
            commits_df[~commits_df["is_author"]]["hour"],
        ],
        [args.author, "Others"],
        show_rug=False,
    )
    hour_distplot.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(
                family="Gilroy Light, Courier New, monospace", size=60, color="#ffffff"
            ),
        )
    )
    hour_distplot.update_xaxes(
        tickangle=45,
        title_text="Hour of the day",
        title_font={"size": 40, "color": "white"},
        title_standoff=25,
        tickfont=dict(color="white", size=40),
    )
    hour_distplot.update_layout(
        {"plot_bgcolor": "rgba(0, 0, 0, 0)", "paper_bgcolor": "rgba(0, 0, 0, 0)"}
    )
    if args.save_plots:
        hour_distplot.write_image(f"{args.plot_prefix}_commit_by_hour.png")

    # Plot the mood
    means_day = (
        author_commits.groupby(["day"])
        .mean()
        .reset_index()
        .rename(
            columns={
                "pos": "Positive",
                "neg": "Negative",
                "neu": "Neutral",
                "compound": "Mood",
            }
        )
    )
    mood_per_day = px.line(
        means_day,
        x="day",
        y=["Positive", "Negative", "Mood"],
        template="plotly_dark",
        line_shape="spline",
    )
    mood_per_day.update_xaxes(
        tickangle=45,
        title_text=" ",
        title_font={"size": 40, "color": "white"},
        title_standoff=25,
        tickfont=dict(color="white", size=40),
    )
    mood_per_day.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(
                family="Gilroy Light, Courier New, monospace", size=60, color="#ffffff"
            ),
            title=None,
        ),
        plot_bgcolor="rgba(0, 0, 0, 0)",
        paper_bgcolor="rgba(0, 0, 0, 0)",
    )
    mood_per_day.update_traces(line=dict(width=10))
    for idx in range(len(mood_per_day.data)):
        mood_per_day.data[idx].x = [
            "Monday",
            "Thuesday",
            "Wednesday",
            "Thursday",
            "Friday",
        ]
    if args.save_plots:
        mood_per_day.write_image(f"{args.plot_prefix}_mood_per_day.png")

    # Histogram showing your means compared to everyone else, removing outliers
    # since they screw up the scale
    # message_quantile = commits_mean['message_length'].quantile(0.90)
    # message_length_histogram = px.histogram(
    #     commits_df[commits_df['message_length'] < message_quantile],
    #     x='message_length',
    #     color='is_author',
    #     title='Message length histogram'
    # )
    # message_length_histogram.show()


def print_dataframe(dataframe, message):
    print(message)
    print(dataframe)
    print("------------------------")


def get_rank_and_value(author, dataframe, column, ascending=False):
    sorted_frame = dataframe.sort_values(by=column, ascending=ascending)
    author_rank = sorted_frame.index.get_loc(author) + 1
    author_value = sorted_frame[column][author]
    return author_rank, author_value


if __name__ == "__main__":
    main()
