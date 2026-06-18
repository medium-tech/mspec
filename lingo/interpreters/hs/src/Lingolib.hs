{-# LANGUAGE OverloadedStrings #-}
module Lingolib
  ( LingoError (..)
  , parseFile
  , executeExe
  , executeFile
  ) where

import           Data.Text (Text, unpack)
import           Data.Yaml (FromJSON (..), decodeFileEither,
                            prettyPrintParseException, withObject, (.:))


-- lingo.spec envelope

data LingoHeader = LingoHeader
  { lingoSpec    :: Text
  , lingoVersion :: Text
  } deriving (Show)

instance FromJSON LingoHeader where
  parseJSON = withObject "LingoHeader" $ \v ->
    LingoHeader <$> v .: "spec" <*> v .: "version"


-- main expression (currently only {str: ...} supported)

newtype MainExpr = MainExprStr Text
  deriving (Show)

instance FromJSON MainExpr where
  parseJSON = withObject "MainExpr" $ \v ->
    MainExprStr <$> v .: "str"


-- exe script document

data ExeScript = ExeScript
  { exeLingo :: LingoHeader
  , exeMain  :: MainExpr
  } deriving (Show)

instance FromJSON ExeScript where
  parseJSON = withObject "ExeScript" $ \v ->
    ExeScript <$> v .: "lingo" <*> v .: "main"


-- public API

newtype LingoError = LingoError String

instance Show LingoError where
  show (LingoError s) = s

parseFile :: FilePath -> IO (Either LingoError ExeScript)
parseFile path = do
  result <- decodeFileEither path
  return $ case result of
    Left  err -> Left  (LingoError (prettyPrintParseException err))
    Right doc -> Right doc

executeExe :: ExeScript -> String
executeExe script =
  let MainExprStr s = exeMain script
  in unpack s

executeFile :: FilePath -> IO (Either LingoError String)
executeFile path = do
  result <- parseFile path
  return $ case result of
    Left  err    -> Left err
    Right script -> Right (executeExe script)
