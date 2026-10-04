package com.worldlive.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.ViewGroup;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.media3.common.MediaItem;
import androidx.media3.common.Player;
import androidx.media3.exoplayer.ExoPlayer;
import androidx.media3.ui.PlayerView;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

public class MainActivity extends Activity {
    private static final int BG = Color.rgb(8, 12, 20);
    private static final int CARD = Color.rgb(19, 26, 39);
    private static final int CARD_2 = Color.rgb(28, 37, 53);
    private static final int TEXT = Color.WHITE;
    private static final int MUTED = Color.rgb(157, 169, 190);
    private static final int ACCENT = Color.rgb(67, 133, 255);
    private static final int LIVE = Color.rgb(239, 68, 68);

    private FrameLayout root;
    private ExoPlayer player;
    private WebView webView;
    private SharedPreferences prefs;

    static class Feed {
        String name, place, type, url;
        Feed(String name, String place, String type, String url) {
            this.name = name;
            this.place = place;
            this.type = type;
            this.url = url;
        }
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        prefs = getSharedPreferences("worldlive_feeds", MODE_PRIVATE);
        root = new FrameLayout(this);
        root.setBackgroundColor(BG);
        setContentView(root);
        showHome();
    }

    private List<Feed> builtIns() {
        List<Feed> f = new ArrayList<>();
        f.add(new Feed("Times Square 4K", "New York • USA", "youtube", "Q0uLV52xGZE"));
        f.add(new Feed("African Safari", "Sabi Sand • South Africa", "youtube", "O81gItg_Jco"));
        f.add(new Feed("Durban Coast Live", "Durban • South Africa", "web", "https://durbancoastlive.com/"));
        f.add(new Feed("Wilderness Beach", "Garden Route • South Africa", "web", "https://www.capetown-webcam.com/garden-route/wilderness-webcam"));
        f.add(new Feed("Tokyo Shibuya", "Tokyo • Japan", "web", "https://www.skylinewebcams.com/en/webcam/japan/kanto/tokyo/shibuya.html"));
        f.add(new Feed("Venice Lagoon", "Venice • Italy", "web", "https://www.skylinewebcams.com/en/webcam/italia/veneto/venezia/bacino-san-marco.html"));
        f.add(new Feed("NASA Live", "Space • Earth Orbit", "web", "https://www.nasa.gov/live/"));
        f.add(new Feed("Global Beach Cams", "Worldwide", "web", "https://worldbeachcams.com/"));
        return f;
    }

    private void showHome() {
        releasePlayback();
        root.removeAllViews();
        ScrollView scroll = new ScrollView(this);
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setPadding(dp(18), dp(18), dp(18), dp(36));
        scroll.addView(page, new ScrollView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        root.addView(scroll, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        TextView logo = text("WORLDLIVE", 30, TEXT, Typeface.BOLD);
        page.addView(logo);
        TextView subtitle = text("Live views from around the world", 15, MUTED, Typeface.NORMAL);
        subtitle.setPadding(0, dp(3), 0, dp(18));
        page.addView(subtitle);

        TextView info = text("DIRECT MODE  •  NO SERVER", 12, Color.rgb(129, 230, 172), Typeface.BOLD);
        info.setGravity(Gravity.CENTER);
        info.setBackground(roundRect(Color.rgb(17, 55, 44), 14));
        LinearLayout.LayoutParams infoLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(40));
        infoLp.setMargins(0, 0, 0, dp(24));
        page.addView(info, infoLp);

        page.addView(section("FEATURED LIVE FEEDS"));
        for (Feed feed : builtIns()) page.addView(feedCard(feed));

        page.addView(section("YOUR DIRECT STREAMS"));
        TextView helper = text("Paste a public HLS (.m3u8), MP4 or compatible stream URL. Streams are saved only on this phone.", 14, MUTED, Typeface.NORMAL);
        helper.setPadding(0, 0, 0, dp(12));
        page.addView(helper);

        Button add = button("+  ADD DIRECT STREAM", ACCENT);
        add.setOnClickListener(v -> showAddDialog());
        LinearLayout.LayoutParams addLp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(52));
        addLp.setMargins(0, 0, 0, dp(14));
        page.addView(add, addLp);

        Set<String> saved = prefs.getStringSet("feeds", null);
        if (saved == null || saved.isEmpty()) {
            TextView empty = text("No custom streams yet.", 14, MUTED, Typeface.NORMAL);
            empty.setPadding(dp(2), dp(10), 0, dp(14));
            page.addView(empty);
        } else {
            for (String item : saved) {
                int split = item.indexOf("|||");
                if (split > 0) {
                    String name = item.substring(0, split);
                    String url = item.substring(split + 3);
                    String host = Uri.parse(url).getHost();
                    page.addView(customFeedCard(new Feed(name, host == null ? "Direct stream" : host, "direct", url), item));
                }
            }
        }

        TextView note = text("Only use public streams or feeds you are authorised to view. Some third-party providers can change or remove their feeds at any time.", 12, MUTED, Typeface.NORMAL);
        note.setPadding(0, dp(18), 0, 0);
        page.addView(note);
    }

    private android.view.View feedCard(Feed feed) {
        LinearLayout card = baseCard();
        LinearLayout top = new LinearLayout(this);
        top.setGravity(Gravity.CENTER_VERTICAL);
        TextView live = text("LIVE", 11, Color.WHITE, Typeface.BOLD);
        live.setGravity(Gravity.CENTER);
        live.setBackground(roundRect(LIVE, 10));
        top.addView(live, new LinearLayout.LayoutParams(dp(50), dp(28)));
        TextView place = text(feed.place, 13, MUTED, Typeface.NORMAL);
        LinearLayout.LayoutParams plp = new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1);
        plp.setMargins(dp(10), 0, 0, 0);
        top.addView(place, plp);
        card.addView(top);

        TextView title = text(feed.name, 20, TEXT, Typeface.BOLD);
        title.setPadding(0, dp(12), 0, dp(8));
        card.addView(title);
        TextView tap = text("Tap to watch  ›", 14, Color.rgb(131, 174, 255), Typeface.BOLD);
        card.addView(tap);
        card.setOnClickListener(v -> openFeed(feed));
        return card;
    }

    private android.view.View customFeedCard(Feed feed, String storedValue) {
        LinearLayout card = baseCard();
        TextView title = text(feed.name, 18, TEXT, Typeface.BOLD);
        card.addView(title);
        TextView place = text(feed.place == null ? "Direct stream" : feed.place, 13, MUTED, Typeface.NORMAL);
        place.setPadding(0, dp(5), 0, dp(12));
        card.addView(place);
        LinearLayout row = new LinearLayout(this);
        Button play = button("PLAY", ACCENT);
        play.setOnClickListener(v -> openFeed(feed));
        row.addView(play, new LinearLayout.LayoutParams(0, dp(44), 1));
        Button del = button("REMOVE", Color.rgb(96, 42, 48));
        LinearLayout.LayoutParams dlp = new LinearLayout.LayoutParams(0, dp(44), 1);
        dlp.setMargins(dp(10), 0, 0, 0);
        row.addView(del, dlp);
        del.setOnClickListener(v -> {
            Set<String> copy = new java.util.HashSet<>(prefs.getStringSet("feeds", new java.util.HashSet<>()));
            copy.remove(storedValue);
            prefs.edit().putStringSet("feeds", copy).apply();
            showHome();
        });
        card.addView(row);
        return card;
    }

    private LinearLayout baseCard() {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(16), dp(16), dp(16), dp(16));
        card.setBackground(roundRect(CARD, 18));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.setMargins(0, 0, 0, dp(12));
        card.setLayoutParams(lp);
        card.setClickable(true);
        card.setFocusable(true);
        return card;
    }

    private TextView section(String label) {
        TextView t = text(label, 13, MUTED, Typeface.BOLD);
        t.setPadding(0, dp(10), 0, dp(12));
        return t;
    }

    private void showAddDialog() {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setPadding(dp(18), dp(8), dp(18), 0);
        EditText name = new EditText(this);
        name.setHint("Stream name");
        name.setSingleLine(true);
        EditText url = new EditText(this);
        url.setHint("https://example.com/live/stream.m3u8");
        url.setSingleLine(true);
        box.addView(name, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        box.addView(url, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        new AlertDialog.Builder(this)
                .setTitle("Add direct stream")
                .setView(box)
                .setNegativeButton("Cancel", null)
                .setPositiveButton("Save", (d, w) -> {
                    String n = name.getText().toString().trim();
                    String u = url.getText().toString().trim();
                    if (n.isEmpty() || u.isEmpty()) {
                        Toast.makeText(this, "Enter a name and stream URL", Toast.LENGTH_SHORT).show();
                        return;
                    }
                    if (!(u.startsWith("http://") || u.startsWith("https://") || u.startsWith("rtsp://"))) {
                        Toast.makeText(this, "Use a valid public stream URL", Toast.LENGTH_SHORT).show();
                        return;
                    }
                    Set<String> copy = new java.util.HashSet<>(prefs.getStringSet("feeds", new java.util.HashSet<>()));
                    copy.add(n + "|||" + u);
                    prefs.edit().putStringSet("feeds", copy).apply();
                    showHome();
                }).show();
    }

    private void openFeed(Feed feed) {
        releasePlayback();
        root.removeAllViews();
        LinearLayout page = new LinearLayout(this);
        page.setOrientation(LinearLayout.VERTICAL);
        page.setBackgroundColor(BG);
        root.addView(page, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));

        LinearLayout bar = new LinearLayout(this);
        bar.setGravity(Gravity.CENTER_VERTICAL);
        bar.setPadding(dp(10), dp(8), dp(12), dp(8));
        bar.setBackgroundColor(CARD);
        Button back = button("‹", CARD_2);
        back.setTextSize(26);
        back.setOnClickListener(v -> showHome());
        bar.addView(back, new LinearLayout.LayoutParams(dp(50), dp(48)));
        LinearLayout titles = new LinearLayout(this);
        titles.setOrientation(LinearLayout.VERTICAL);
        titles.setPadding(dp(12), 0, 0, 0);
        titles.addView(text(feed.name, 17, TEXT, Typeface.BOLD));
        titles.addView(text(feed.place, 12, MUTED, Typeface.NORMAL));
        bar.addView(titles, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1));
        page.addView(bar, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(66)));

        TextView banner = text("● LIVE", 12, Color.WHITE, Typeface.BOLD);
        banner.setGravity(Gravity.CENTER);
        banner.setBackgroundColor(LIVE);
        page.addView(banner, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(28)));

        if ("direct".equals(feed.type)) {
            PlayerView playerView = new PlayerView(this);
            playerView.setUseController(true);
            playerView.setShowBuffering(PlayerView.SHOW_BUFFERING_WHEN_PLAYING);
            player = new ExoPlayer.Builder(this).build();
            playerView.setPlayer(player);
            player.setMediaItem(MediaItem.fromUri(feed.url));
            player.prepare();
            player.setPlayWhenReady(true);
            player.addListener(new Player.Listener() {
                @Override public void onPlayerError(androidx.media3.common.PlaybackException error) {
                    Toast.makeText(MainActivity.this, "Stream could not be played. It may be offline or restricted.", Toast.LENGTH_LONG).show();
                }
            });
            page.addView(playerView, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));
        } else {
            webView = new WebView(this);
            WebSettings s = webView.getSettings();
            s.setJavaScriptEnabled(true);
            s.setDomStorageEnabled(true);
            s.setMediaPlaybackRequiresUserGesture(false);
            s.setLoadsImagesAutomatically(true);
            s.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);
            webView.setBackgroundColor(Color.BLACK);
            webView.setWebViewClient(new WebViewClient());
            webView.setWebChromeClient(new WebChromeClient());
            if ("youtube".equals(feed.type)) {
                String html = "<html><body style='margin:0;background:#000'><iframe width='100%' height='100%' src='https://www.youtube.com/embed/" + feed.url + "?autoplay=1&playsinline=1&rel=0' frameborder='0' allow='autoplay; encrypted-media; picture-in-picture' allowfullscreen></iframe></body></html>";
                webView.loadDataWithBaseURL("https://www.youtube.com", html, "text/html", "UTF-8", null);
            } else {
                webView.loadUrl(feed.url);
            }
            page.addView(webView, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1));
        }
    }

    private void releasePlayback() {
        if (player != null) {
            player.release();
            player = null;
        }
        if (webView != null) {
            webView.stopLoading();
            webView.loadUrl("about:blank");
            webView.destroy();
            webView = null;
        }
    }

    @Override public void onBackPressed() {
        if (webView != null || player != null) showHome(); else super.onBackPressed();
    }

    @Override protected void onDestroy() {
        releasePlayback();
        super.onDestroy();
    }

    private TextView text(String value, int sp, int color, int style) {
        TextView t = new TextView(this);
        t.setText(value);
        t.setTextSize(sp);
        t.setTextColor(color);
        t.setTypeface(Typeface.create("sans-serif", style));
        return t;
    }

    private Button button(String value, int color) {
        Button b = new Button(this);
        b.setText(value);
        b.setTextColor(Color.WHITE);
        b.setTextSize(13);
        b.setTypeface(Typeface.create("sans-serif", Typeface.BOLD));
        b.setAllCaps(false);
        b.setBackground(roundRect(color, 14));
        return b;
    }

    private android.graphics.drawable.GradientDrawable roundRect(int color, int radiusDp) {
        android.graphics.drawable.GradientDrawable g = new android.graphics.drawable.GradientDrawable();
        g.setColor(color);
        g.setCornerRadius(dp(radiusDp));
        return g;
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }
}
