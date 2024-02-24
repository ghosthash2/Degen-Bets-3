/* eslint-disable @typescript-eslint/no-var-requires */
import { Controller, Get, Injectable, Param } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import axios from 'axios';

const fs = require('fs');

function shortStringGames(str: string): string {
  // Split the string into words
  const words = str.split('_');
  // Create an empty array to store the last letter of each word
  const letters: string[] = [];
  // Iterate over each word in the array
  for (const word of words) {
    // Append the last letter of the word to the array
    letters.push(word[word.length - 1]);
  }
  // Join the letters together and convert to uppercase
  const short = letters.join('').toUpperCase();
  // Return the short string
  return short;
}

function shortStringMatch(str: string): string {
  let newStr = '';
  for (let i = 2; i < str.length; i += 3) {
    newStr += str[i].toUpperCase();
  }
  return newStr;
}

async function getCachedData(url: string, cacheDays: number): Promise<any> {
  console.log('Check for chache, ', url);
  const cacheDir = __dirname + '/cache'; // Directory to store cached data
  const cacheFile = cacheDir + '/' + encodeURIComponent(url); // Cache file path

  // Check if cache directory exists, create it if not
  if (!fs.existsSync(cacheDir)) {
    fs.mkdirSync(cacheDir);
  }

  // Check if cache file exists and is not expired
  if (fs.existsSync(cacheFile)) {
    const stats = fs.statSync(cacheFile);
    const cacheAge = Math.ceil(
      (Date.now() - stats.mtimeMs) / (1000 * 3600 * 24),
    ); // Calculate cache age in days

    if (cacheAge <= cacheDays) {
      const cachedData = fs.readFileSync(cacheFile, 'utf8');
      console.log('returning from cache, ', url);
      return JSON.parse(cachedData);
    }
  }

  // If cache file doesn't exist or is expired, make the API call and cache the response
  console.log('not in cache, ', url);
  const response = await axios.get(url);
  fs.writeFileSync(cacheFile, JSON.stringify(response.data), 'utf8');

  return response.data;
}

@Injectable()
@Controller('sports')
export class SportsController {
  constructor(private configService: ConfigService) { }

  @Get()
  async getSports(): Promise<string> {
    try {
      const url = `https://api.the-odds-api.com/v4/sports?apiKey=${this.configService.get<string>(
        'ODDS_API_KEY',
      )}`;

      const response = await getCachedData(url, 32);

      const newV = [];
      response.forEach((element) => {
        newV.push({ ...element, keyTG: shortStringGames(element['key']) });
      });

      return JSON.stringify(newV);
    } catch (error) {
      console.error(error);
      console.log('Error message: ', error.message);
      console.log('Error stack: ', error.stack);
    }
  }

  @Get('/:sportId')
  async getMatches(@Param() params: { sportId: string }): Promise<string> {
    try {
      const url = `https://api.the-odds-api.com/v4/sports/${params.sportId
        }/scores/?daysFrom=3&apiKey=${this.configService.get<string>(
          'ODDS_API_KEY',
        )}`;

      // Call the caching function instead of directly calling axios.get
      const response = await getCachedData(url, 32);

      const newV = [];
      response.forEach((element) => {
        newV.push({ ...element, idTG: shortStringMatch(element['id']) });
      });

      return JSON.stringify(newV);
    } catch (error) {
      console.error(error);
      console.log('Error message: ', error.message);
      console.log('Error stack: ', error.stack);
    }
  }
}
