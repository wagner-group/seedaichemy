#!/bin/bash

PROGRAM="openssl"

mkdir SeedAIchemy/$PROGRAM

for TARGET in "asn1" "asn1parse" "bignum" "client" "server" "x509"; do
    mkdir SeedAIchemy/$PROGRAM/$TARGET
    for i in {0..9}; do 
        mkdir SeedAIchemy/$PROGRAM/$TARGET/$i
        tar -xf "/data2/jingzhijiang/magma_experiment_result/llm_corpus_experiment/llm_corpus_experiment_aggregate/trial_$((i+1))/llm_corpus_experiment_1/ar/aflplusplus/$PROGRAM/$TARGET/0/ball.tar" --strip-components=3 -C "SeedAIchemy/$PROGRAM/$TARGET/$i/" "./findings/default/plot_data"
    done
done


