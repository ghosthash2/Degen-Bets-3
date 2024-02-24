import { Injectable } from '@nestjs/common';
import { Response } from 'express';
import axios from 'axios';
import { IsNull, Not, Repository } from 'typeorm';
import { Bet } from './bets.entity';
import { InjectRepository } from '@nestjs/typeorm';
import { ConfigService } from '@nestjs/config';
import { retrieveWalletAddressFromSig } from '../utils/signature';
import { MongoClient } from 'mongodb';

@Injectable()
export class BetsService {
  constructor(
    @InjectRepository(Bet)
    private betsRepository: Repository<Bet>,
    private configService: ConfigService,
  ) { }

  async createBet(
    {
      sport,
      matchId,
      value,
      signature,
      validTill,
      homeToWin,
      groupId,
    }: {
      sport: string;
      matchId: string;
      value: number;
      signature: string;
      validTill: number;
      homeToWin: boolean;
      groupId: string;
    },
    res: Response,
  ): Promise<Response> {
    const wallet = retrieveWalletAddressFromSig(signature);
    console.log(`Request to create bet by wallet: ${wallet}`);
    if (!wallet) {
      return res.sendStatus(401);
    }

    const response = await axios.get(
      `https://api.the-odds-api.com/v4/sports/${sport}/scores/?daysFrom=3&apiKey=${this.configService.get<string>(
        'ODDS_API_KEY',
      )}`,
    );
    const matchExists = response.data.some((match) => match.id === matchId);
    if (!matchExists) {
      res.status(400);
      return res.json({ message: `Match with ${matchId} does not exist` });
    }

    if (validTill <= Date.now()) {
      res.json({
        message: `The validTill date should be in the future, you sent ${new Date(
          validTill,
        ).toISOString()}`,
      });
    }

    const bet = await this.betsRepository.save({
      matchId,
      value,
      sport,
      groupId: groupId,
      creatorId: wallet,
      validTill: new Date(validTill),
      homeToWin,
    });
    res.status(201);
    res.json(bet);
  }

  async acceptBet(
    { id, signature }: { id: string; signature: string },
    res: Response,
  ): Promise<Response> {
    const wallet = retrieveWalletAddressFromSig(signature);
    console.log(`Request to accept bet with id: ${id} by wallet: ${wallet}`);
    if (!wallet) {
      return res.sendStatus(401);
    }

    const bet = await this.betsRepository.update(
      {
        id,
      },
      {
        competitorId: wallet,
      },
    );

    res.status(200);
    res.json(bet);
  }

  async settleBets(sport: string, res: Response): Promise<Response> {
    const response = await axios.get(
      `https://api.the-odds-api.com/v4/sports/${sport}/scores/?daysFrom=3&apiKey=${this.configService.get<string>(
        'ODDS_API_KEY',
      )}`,
    );
    for (const match of response.data) {
      const bets = await this.betsRepository.find({
        where: {
          completed: false,
          matchId: match.id,
          competitorId: Not(IsNull()),
        },
      });
      for (const bet of bets) {
        if (match.scores !== null) {
          const homeScore = match.scores.find(
            (score) => score.name === match.home_team,
          ).score;
          const awayScore = match.scores.find(
            (score) => score.name === match.away_team,
          ).score;
          console.log(
            `For bet with id ${bet.id}, the home score was ${homeScore} and away score was ${awayScore}`,
          );
          const homeWon = homeScore > awayScore;
          await this.betsRepository.update(
            {
              id: bet.id,
            },
            {
              completed: true,
              winnerId:
                bet.homeToWin === homeWon ? bet.creatorId : bet.competitorId,
            },
          );

          // write code that updates the balance on mondo db

          const uri = process.env.MONGODB_URI;
          const client = new MongoClient(uri);

          try {
            await client.connect();
            const database = client.db(process.env.MONGODB_DB);
            const collection = database.collection(
              process.env.MONGODB_COLLECTION,
            );

            // winner gets 2x the value
            const query = {
              wallet_address:
                bet.homeToWin === homeWon ? bet.creatorId : bet.competitorId,
            };
            const update = { $inc: { balance: bet.value * 2 } };
            const resultIncWinner = await collection.updateOne(query, update);

            console.log(
              `Successfully updated the balance of user with wallet address ${bet.competitorId}`,
            );
          } catch (err) {
            console.error(err);
          } finally {
            await client.close();
          }
        }
      }
    }
    return res.sendStatus(204);
  }

  async getAllActiveBets(res: Response): Promise<Response> {
    const bets = await this.betsRepository.find();
    res.status(200);
    return res.json(bets);
  }
}
