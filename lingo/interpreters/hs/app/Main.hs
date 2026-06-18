module Main where

import Lingolib (executeFile)
import System.Environment (getArgs)
import System.Exit (exitFailure, exitSuccess)
import System.IO (hPutStrLn, stderr)


helpText :: String
helpText = unlines
    [ "usage: lingolib [--help] <command> [args]"
    , ""
    , "commands:"
    , "  exe <path>    load, parse, execute an exe spec and print result"
    , ""
    , "supported specs: exe"
    ]

main :: IO ()
main = do
    args <- getArgs
    case args of
        []            -> putStr helpText >> exitSuccess
        ["-h"]        -> putStr helpText >> exitSuccess
        ["--help"]    -> putStr helpText >> exitSuccess
        ("exe":path:_) -> do
            result <- executeFile path
            case result of
                Left  err -> hPutStrLn stderr ("error: " ++ show err) >> exitFailure
                Right val -> putStrLn val
        ["exe"] ->
            hPutStrLn stderr "error: exe requires a path argument" >> exitFailure
        (cmd:_) ->
            hPutStrLn stderr ("error: unknown command: " ++ show cmd) >> exitFailure
