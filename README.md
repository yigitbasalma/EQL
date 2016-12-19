# EQL
## Amaç
Web server ve uygulama arasında yer alarak gelen istekleri karşılamak ve backend sunuculara daha az yük gitmesini sağlamak.
## Yapı
Web server ve uygulama arasında yer alarak gelen istekleri karşılar ve sonrasında couchbase içerisinde istenen key var mı diye kontrol eder.( Varsayılan olarak key, istek yapılan URL in md5 hashlenmiş halidir. ) Eğer istek yapılan item bucketta yer alıyorsa istek cacheden cevaplanır.Uygulama iki ana bucket kullanır.
+ cache_bucket : Itemlerin tutulduğu ana buckettır.Data, bytarray halinde burada tutulur.
+ statistic_bucket : Burada cachelenen iteme ait istatisliksel bilgiler tutulmaktadır.Liste formatında olan bu data sırasıyla,
  + iteme kaç kere istek geldi,
  + cache ne zaman oluştu,
  + iteme ait mime type bilgisi.
