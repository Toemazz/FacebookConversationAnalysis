# https://i.imgur.com/QfbOt87.png
import math
import pickle
import ntpath
import matplotlib
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from bs4 import BeautifulSoup
from datetime import datetime as dt
from dateutil import relativedelta
from tqdm import tqdm as tq
from collections import Counter

matplotlib.use('Qt5Agg')
plt.style.use('ggplot')
rcParams.update({'figure.autolayout': True})


class FacebookConversationAnalysis:
    def __init__(self, html_file, get_data=False):
        # Datetime formats
        self.full_date_format = '%A, %d %B %Y at %H:%M %Z'
        self.date_format = '%d/%m/%y'
        self.time_format = '%H:%M'

        pickle_file_names = ['pickles/senders.pickle', 'pickles/messages.pickle',
                             'pickles/dates.pickle', 'pickles/times.pickle']

        if get_data:
            data = self.extract_data_from_html_file(html_file)

            for n, name in enumerate(pickle_file_names):
                self.save_pickle(data[n], name)
        else:
            data = []
            for name in pickle_file_names:
                data.append(self.load_pickle(name))

        self.users, self.msgs, self.dates, self.times = data[0], data[1], data[2], data[3]

        self.total_msgs = len(self.msgs)

    # Method: Used to 'pickle' a list of data
    @staticmethod
    def save_pickle(data, name):
        with open(name, 'wb') as f:
            pickle.dump(data, f)
        print('[INFO]: {} saved'.format(ntpath.basename(name)))

    # Method: Used to load a 'pickle'
    @staticmethod
    def load_pickle(name):
        with open(name, 'rb') as f:
            print('[INFO]: {} loaded'.format(ntpath.basename(name)))
            return pickle.load(f)

    # Method: Used to extract message data from Facebook HTML file
    def extract_data_from_html_file(self, html_file):
        print('[INFO]: Extracting data from {}'.format(html_file))
        soup = BeautifulSoup(open(html_file, encoding='utf8'), 'lxml')

        users, msgs, dates, times = [], [], [], []

        # Find 'thread' tags
        for thread in soup.find_all(class_='thread'):
            # Find 'message' tags
            for chat in tq(thread.find_all(class_='message'), desc='Chats'):
                # Extract sender and message
                user = str(chat.find(class_='user').string)
                msg = str(chat.next_sibling.string)

                # Extract date and time
                full_date = dt.strptime(chat.find(class_='meta').string.replace("+01", ""), self.full_date_format)
                date = str(full_date.strftime(self.date_format))
                time = str(full_date.strftime(self.time_format))

                # Ignore 'pictures'
                if msg != 'None':
                    users.append(user)
                    msgs.append(msg)
                    dates.append(date)
                    times.append(time)

        print('[INFO]: Data extracted from {}'.format(html_file))
        return [users, msgs, dates, times]

    # Method: Used to calculate the number of messages by each user
    def calculate_total_messages_per_user(self):
        msgs_freq = dict(Counter(self.users))
        unique_users, messages_per_user = zip(*sorted(msgs_freq.items()))

        for i in range(len(unique_users)):
            msgs_percentage = (messages_per_user[i] / self.total_msgs) * 100
            print('[INFO]: Messages sent by {}: {} ({:.1f}%)'.format(unique_users[i], messages_per_user[i], msgs_percentage))

        return unique_users, messages_per_user

    # Method: Used to calculate the average number of words per message
    def calculate_average_words_per_message(self):
        total_words = 0

        for msg in self.msgs:
            total_words += len(msg.split())

        avg_words_per_msg = float(total_words / self.total_msgs)
        print('[INFO]: Average Words/Message: {:.2f}'.format(avg_words_per_msg))

    # Method: Used to calculate the average number of messages per unit time
    def calculate_average_messages_per_unit_time(self, unit_time='day'):
        first_date = dt.strptime(self.dates[-1], self.date_format)
        last_date = dt.strptime(self.dates[0], self.date_format)

        delta_dt = last_date - first_date
        delta_du = relativedelta.relativedelta(last_date, first_date)

        if unit_time not in ['day', 'week', 'month', 'year']:
            print('[ERROR]: Please choose a correct value for unit_time')
        else:
            if unit_time == 'day':
                interval = delta_dt.days
            elif unit_time == 'week':
                interval = math.ceil(delta_dt.days / 7)
            elif unit_time == 'month':
                interval = delta_du.years*12 + delta_du.months
            else:
                interval = delta_du.years

            avg_messages_per_unit_time = float(self.total_msgs / interval)
            print('[INFO]: Average Messages/{}: {:.1f}'.format(unit_time.title(), avg_messages_per_unit_time))
            return avg_messages_per_unit_time

    # Method: Used to find the day with most
    def find_most_active_day(self):
        dates_freq = dict(Counter(self.dates))

        date = max(dates_freq, key=dates_freq.get)
        num_msgs = max(dates_freq.values())
        seconds_per_msg = 86400 / num_msgs

        print('[INFO]: Most active day was {} with {} messages sent. Thats a message every {:.2f} seconds!'
              .format(date, num_msgs, seconds_per_msg))

    # Method: Used to plot the total messages per hour
    def plot_average_messages_per_hour(self, save_path='graphs/AverageMessagesPerHour.png',
                                       title='Average Messages/Hour',
                                       x_label='Hours', y_label='Number of Messages'):
        delta = dt.strptime(self.dates[0], self.date_format) - dt.strptime(self.dates[-1], self.date_format)

        # Extract the hour from the time
        hrs = [time[:2] for time in self.times]

        # Calculate total number of messages per hour
        hours_freq = dict(Counter(hrs))
        hours, total_msgs_per_hour = zip(*sorted(hours_freq.items()))

        # Calculate the average number of messages per hour
        avg_msgs_per_hour = [(hour_msgs / int(delta.days)) for hour_msgs in total_msgs_per_hour]

        # Plot number of total messages per hour
        plt.bar(range(len(avg_msgs_per_hour)), avg_msgs_per_hour)
        for i, avg_msgs in enumerate(avg_msgs_per_hour):
            plt.text(i-0.5, avg_msgs+1, '{:.1f}'.format(avg_msgs), fontsize='smaller')
        plt.xticks(range(len(hours)), hours)
        plt.xlim([-0.5, len(hours)-0.5])
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.title(title)
        plt.savefig(save_path)
        plt.show()

    # Method: Used to plot the total messages per hour
    def plot_average_messages_per_weekday(self, save_path='graphs/AverageMessagesPerWeekday.png',
                                          title='Average Messages/Weekday',
                                          x_label='Weekday', y_label='Number of Messages'):
        msgs_per_weekday = [0] * 7
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        # Get dates and associated times for each day of the week
        for i in range(len(self.dates)):
            date = dt.strptime(self.dates[i], self.date_format)

            if date.weekday() == 0:
                msgs_per_weekday[date.weekday()] += 1
            elif date.weekday() == 1:
                msgs_per_weekday[date.weekday()] += 1
            elif date.weekday() == 2:
                msgs_per_weekday[date.weekday()] += 1
            elif date.weekday() == 3:
                msgs_per_weekday[date.weekday()] += 1
            elif date.weekday() == 4:
                msgs_per_weekday[date.weekday()] += 1
            elif date.weekday() == 5:
                msgs_per_weekday[date.weekday()] += 1
            else:
                msgs_per_weekday[date.weekday()] += 1

        avg_msgs_per_weekday = [weekday_msgs / 7 for weekday_msgs in msgs_per_weekday]

        # Plot average number of messages per hour
        plt.bar(range(len(avg_msgs_per_weekday)), avg_msgs_per_weekday)
        for i, msgs in enumerate(avg_msgs_per_weekday):
            plt.text(i-0.25, msgs+2, '{:.1f}'.format(msgs))
        plt.xticks(range(len(weekdays)), weekdays)
        plt.xlim([-0.5, len(weekdays)-0.5])
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.title(title)
        plt.savefig(save_path)
        plt.show()

    # Method: Used to plot the ratio of total messages sent per user
    def plot_total_messages_per_user(self, save_path='graphs/TotalMessagesPerUser.png', title='Total Messages/User'):
        usrs, msgs = self.calculate_total_messages_per_user()
        usrs_first_name = [usr.split()[0] for usr in usrs]

        # Pie chart
        plt.pie(msgs, shadow=True, explode=(0.05, 0.05), autopct='%1.1f%%')
        plt.legend(labels=usrs_first_name, loc="best")
        plt.axis('equal')
        plt.title(title)
        plt.savefig(save_path)
        plt.show()

    # Method: Used to plot the daily activity over the full time period
    def plot_activity(self, save_path='graphs/Activity.png', title='Total Messages/Day', x_label='Weekday',
                      y_label='Date'):
        dates = [dt.strptime(date, self.date_format) for date in self.dates]
        dates = [date_dt.strftime('%Y/%m/%d') for date_dt in dates]
        dates = sorted(dates, key=lambda x: dt.strptime(x, '%Y/%m/%d'))

        dates_freq = dict(Counter(dates))
        unique_dates, msgs_per_date = zip(*sorted(dates_freq.items()))

        unique_dates = [date[:7] for date in unique_dates]

        def moving_average(interval, window_size):
            window = np.ones(int(window_size)) / float(window_size)
            return np.convolve(interval, window, 'same')

        # Plot average number of messages per hour
        plt.plot(range(len(msgs_per_date)), msgs_per_date)
        plt.plot(range(len(msgs_per_date)), moving_average(msgs_per_date, 30))
        plt.axhline(y=self.calculate_average_messages_per_unit_time('day'), color='g')
        plt.xticks(range(len(unique_dates)), unique_dates[0::30], rotation=60)
        plt.locator_params(axis='x', nbins=len(unique_dates[0::60]))
        plt.xlim([-0.5, len(unique_dates)-0.5])
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.title(title)
        plt.legend(labels=['Daily Total', 'Rolling Average', 'Average'], loc='best')
        plt.savefig(save_path)
        plt.show()


if __name__ == '__main__':
    # Create instance and get data
    fb = FacebookConversationAnalysis('171.html')

    # Calculate some statistics
    # fb.calculate_total_messages_per_user()
    # fb.calculate_average_words_per_message()
    # fb.calculate_average_messages_per_unit_time('day')
    # fb.calculate_average_messages_per_unit_time('week')
    # fb.calculate_average_messages_per_unit_time('month')
    # fb.calculate_average_messages_per_unit_time('year')
    # fb.find_most_active_day()

    # Plot some graphs
    # fb.plot_average_messages_per_hour()
    # fb.plot_average_messages_per_weekday()
    # fb.plot_total_messages_per_user()
    fb.plot_activity()

