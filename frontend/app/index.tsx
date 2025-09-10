import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  Alert,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import * as Speech from 'expo-speech';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width, height } = Dimensions.get('window');
const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface Translation {
  word: string;
  bengaliTranslation: string;
  pronunciation: string;
  definition: string;
  examples: string[];
  partOfSpeech: string;
  timestamp: string;
}

interface SearchHistory {
  id: string;
  word: string;
  timestamp: string;
}

export default function Index() {
  const [searchTerm, setSearchTerm] = useState('');
  const [translation, setTranslation] = useState<Translation | null>(null);
  const [loading, setLoading] = useState(false);
  const [favorites, setFavorites] = useState<Translation[]>([]);
  const [history, setHistory] = useState<SearchHistory[]>([]);
  const [activeTab, setActiveTab] = useState<'search' | 'favorites' | 'history'>('search');

  useEffect(() => {
    loadFavorites();
    loadHistory();
  }, []);

  const loadFavorites = async () => {
    try {
      const savedFavorites = await AsyncStorage.getItem('favorites');
      if (savedFavorites) {
        setFavorites(JSON.parse(savedFavorites));
      }
    } catch (error) {
      console.error('Error loading favorites:', error);
    }
  };

  const loadHistory = async () => {
    try {
      const savedHistory = await AsyncStorage.getItem('searchHistory');
      if (savedHistory) {
        setHistory(JSON.parse(savedHistory));
      }
    } catch (error) {
      console.error('Error loading history:', error);
    }
  };

  const saveFavorite = async (translation: Translation) => {
    try {
      const isFavorite = favorites.some(fav => fav.word === translation.word);
      let updatedFavorites;
      
      if (isFavorite) {
        updatedFavorites = favorites.filter(fav => fav.word !== translation.word);
        Alert.alert('Removed from favorites');
      } else {
        updatedFavorites = [...favorites, translation];
        Alert.alert('Added to favorites');
      }
      
      setFavorites(updatedFavorites);
      await AsyncStorage.setItem('favorites', JSON.stringify(updatedFavorites));
    } catch (error) {
      console.error('Error saving favorite:', error);
    }
  };

  const saveToHistory = async (word: string) => {
    try {
      const newHistoryItem: SearchHistory = {
        id: Date.now().toString(),
        word,
        timestamp: new Date().toISOString(),
      };
      
      const updatedHistory = [newHistoryItem, ...history.slice(0, 49)]; // Keep last 50 searches
      setHistory(updatedHistory);
      await AsyncStorage.setItem('searchHistory', JSON.stringify(updatedHistory));
    } catch (error) {
      console.error('Error saving to history:', error);
    }
  };

  const searchWord = async (word: string) => {
    if (!word.trim()) return;
    
    setLoading(true);
    try {
      const response = await fetch(`${EXPO_PUBLIC_BACKEND_URL}/api/translate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ word: word.trim() }),
      });

      if (response.ok) {
        const data = await response.json();
        setTranslation(data);
        await saveToHistory(word.trim());
      } else {
        Alert.alert('Error', 'Failed to get translation');
      }
    } catch (error) {
      console.error('Translation error:', error);
      Alert.alert('Error', 'Network error. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  const speakText = (text: string, language: 'en' | 'bn' = 'en') => {
    Speech.speak(text, {
      language: language === 'en' ? 'en-US' : 'bn-BD',
      pitch: 1.0,
      rate: 0.8,
    });
  };

  const clearHistory = async () => {
    Alert.alert(
      'Clear History',
      'Are you sure you want to clear all search history?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear',
          style: 'destructive',
          onPress: async () => {
            setHistory([]);
            await AsyncStorage.removeItem('searchHistory');
          },
        },
      ]
    );
  };

  const renderSearchTab = () => (
    <View style={styles.tabContent}>
      <View style={styles.searchContainer}>
        <View style={styles.searchInputContainer}>
          <Ionicons name="search" size={20} color="#64FFDA" style={styles.searchIcon} />
          <TextInput
            style={styles.searchInput}
            placeholder="Enter English word..."
            placeholderTextColor="#666"
            value={searchTerm}
            onChangeText={setSearchTerm}
            onSubmitEditing={() => searchWord(searchTerm)}
            returnKeyType="search"
          />
          {searchTerm.length > 0 && (
            <TouchableOpacity
              onPress={() => setSearchTerm('')}
              style={styles.clearButton}
            >
              <Ionicons name="close-circle" size={20} color="#666" />
            </TouchableOpacity>
          )}
        </View>
        
        <TouchableOpacity
          style={styles.searchButton}
          onPress={() => searchWord(searchTerm)}
          disabled={loading}
        >
          <LinearGradient
            colors={['#64FFDA', '#00BCD4']}
            style={styles.searchButtonGradient}
          >
            {loading ? (
              <ActivityIndicator color="#000" size="small" />
            ) : (
              <Ionicons name="search" size={20} color="#000" />
            )}
          </LinearGradient>
        </TouchableOpacity>
      </View>

      {translation && (
        <View style={styles.translationCard}>
          <LinearGradient
            colors={['rgba(100, 255, 218, 0.1)', 'rgba(0, 188, 212, 0.1)']}
            style={styles.cardGradient}
          >
            <View style={styles.cardHeader}>
              <View style={styles.wordSection}>
                <Text style={styles.englishWord}>{translation.word}</Text>
                <Text style={styles.pronunciation}>/{translation.pronunciation}/</Text>
                <Text style={styles.partOfSpeech}>{translation.partOfSpeech}</Text>
              </View>
              
              <View style={styles.actionButtons}>
                <TouchableOpacity
                  onPress={() => speakText(translation.word)}
                  style={styles.actionButton}
                >
                  <Ionicons name="volume-high" size={20} color="#64FFDA" />
                </TouchableOpacity>
                
                <TouchableOpacity
                  onPress={() => saveFavorite(translation)}
                  style={styles.actionButton}
                >
                  <Ionicons 
                    name={favorites.some(fav => fav.word === translation.word) ? "heart" : "heart-outline"} 
                    size={20} 
                    color="#FF6B6B" 
                  />
                </TouchableOpacity>
              </View>
            </View>

            <View style={styles.translationSection}>
              <Text style={styles.bengaliText}>{translation.bengaliTranslation}</Text>
              <TouchableOpacity
                onPress={() => speakText(translation.bengaliTranslation, 'bn')}
                style={styles.speakBengali}
              >
                <Ionicons name="volume-high" size={16} color="#64FFDA" />
              </TouchableOpacity>
            </View>

            <Text style={styles.definition}>{translation.definition}</Text>

            {translation.examples && translation.examples.length > 0 && (
              <View style={styles.examplesSection}>
                <Text style={styles.examplesTitle}>Examples:</Text>
                {translation.examples.map((example, index) => (
                  <Text key={index} style={styles.example}>• {example}</Text>
                ))}
              </View>
            )}
          </LinearGradient>
        </View>
      )}
    </View>
  );

  const renderFavoritesTab = () => (
    <ScrollView style={styles.tabContent}>
      <Text style={styles.tabTitle}>Favorite Words</Text>
      {favorites.length === 0 ? (
        <View style={styles.emptyState}>
          <Ionicons name="heart-outline" size={64} color="#333" />
          <Text style={styles.emptyText}>No favorites yet</Text>
          <Text style={styles.emptySubtext}>Tap the heart icon on translations to save them</Text>
        </View>
      ) : (
        favorites.map((fav, index) => (
          <TouchableOpacity
            key={index}
            style={styles.favoriteItem}
            onPress={() => {
              setTranslation(fav);
              setActiveTab('search');
            }}
          >
            <LinearGradient
              colors={['rgba(255, 107, 107, 0.1)', 'rgba(255, 107, 107, 0.05)']}
              style={styles.favoriteCard}
            >
              <View style={styles.favoriteContent}>
                <Text style={styles.favoriteWord}>{fav.word}</Text>
                <Text style={styles.favoriteBengali}>{fav.bengaliTranslation}</Text>
              </View>
              <TouchableOpacity
                onPress={(e) => {
                  e.stopPropagation();
                  saveFavorite(fav);
                }}
              >
                <Ionicons name="heart" size={20} color="#FF6B6B" />
              </TouchableOpacity>
            </LinearGradient>
          </TouchableOpacity>
        ))
      )}
    </ScrollView>
  );

  const renderHistoryTab = () => (
    <ScrollView style={styles.tabContent}>
      <View style={styles.historyHeader}>
        <Text style={styles.tabTitle}>Search History</Text>
        {history.length > 0 && (
          <TouchableOpacity onPress={clearHistory} style={styles.clearHistoryButton}>
            <Text style={styles.clearHistoryText}>Clear All</Text>
          </TouchableOpacity>
        )}
      </View>
      
      {history.length === 0 ? (
        <View style={styles.emptyState}>
          <Ionicons name="time-outline" size={64} color="#333" />
          <Text style={styles.emptyText}>No search history</Text>
          <Text style={styles.emptySubtext}>Your searched words will appear here</Text>
        </View>
      ) : (
        history.map((item) => (
          <TouchableOpacity
            key={item.id}
            style={styles.historyItem}
            onPress={() => {
              setSearchTerm(item.word);
              searchWord(item.word);
              setActiveTab('search');
            }}
          >
            <LinearGradient
              colors={['rgba(100, 255, 218, 0.05)', 'rgba(0, 188, 212, 0.05)']}
              style={styles.historyCard}
            >
              <Ionicons name="time" size={16} color="#64FFDA" />
              <Text style={styles.historyWord}>{item.word}</Text>
              <Text style={styles.historyTime}>
                {new Date(item.timestamp).toLocaleDateString()}
              </Text>
            </LinearGradient>
          </TouchableOpacity>
        ))
      )}
    </ScrollView>
  );

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0a0a0a" />
      
      <LinearGradient
        colors={['#0a0a0a', '#1a1a2e', '#16213e']}
        style={styles.background}
      >
        <View style={styles.header}>
          <Text style={styles.headerTitle}>AI Dictionary</Text>
          <Text style={styles.headerSubtitle}>English ↔ Bengali</Text>
        </View>

        <View style={styles.content}>
          {activeTab === 'search' && renderSearchTab()}
          {activeTab === 'favorites' && renderFavoritesTab()}
          {activeTab === 'history' && renderHistoryTab()}
        </View>

        <View style={styles.bottomNav}>
          <TouchableOpacity
            style={[styles.navButton, activeTab === 'search' && styles.activeNavButton]}
            onPress={() => setActiveTab('search')}
          >
            <Ionicons 
              name="search" 
              size={24} 
              color={activeTab === 'search' ? '#64FFDA' : '#666'} 
            />
            <Text style={[styles.navText, activeTab === 'search' && styles.activeNavText]}>
              Search
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.navButton, activeTab === 'favorites' && styles.activeNavButton]}
            onPress={() => setActiveTab('favorites')}
          >
            <Ionicons 
              name="heart" 
              size={24} 
              color={activeTab === 'favorites' ? '#FF6B6B' : '#666'} 
            />
            <Text style={[styles.navText, activeTab === 'favorites' && styles.activeNavText]}>
              Favorites
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.navButton, activeTab === 'history' && styles.activeNavButton]}
            onPress={() => setActiveTab('history')}
          >
            <Ionicons 
              name="time" 
              size={24} 
              color={activeTab === 'history' ? '#FFA726' : '#666'} 
            />
            <Text style={[styles.navText, activeTab === 'history' && styles.activeNavText]}>
              History
            </Text>
          </TouchableOpacity>
        </View>
      </LinearGradient>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0a0a0a',
  },
  background: {
    flex: 1,
  },
  header: {
    paddingTop: 20,
    paddingHorizontal: 20,
    paddingBottom: 30,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#64FFDA',
    textAlign: 'center',
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#999',
    marginTop: 5,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  tabContent: {
    flex: 1,
  },
  tabTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 20,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  searchInputContainer: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 25,
    paddingHorizontal: 15,
    borderWidth: 1,
    borderColor: 'rgba(100, 255, 218, 0.3)',
  },
  searchIcon: {
    marginRight: 10,
  },
  searchInput: {
    flex: 1,
    height: 50,
    color: '#fff',
    fontSize: 16,
  },
  clearButton: {
    padding: 5,
  },
  searchButton: {
    marginLeft: 15,
  },
  searchButtonGradient: {
    width: 50,
    height: 50,
    borderRadius: 25,
    alignItems: 'center',
    justifyContent: 'center',
  },
  translationCard: {
    marginTop: 20,
  },
  cardGradient: {
    borderRadius: 20,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(100, 255, 218, 0.2)',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 15,
  },
  wordSection: {
    flex: 1,
  },
  englishWord: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5,
  },
  pronunciation: {
    fontSize: 16,
    color: '#64FFDA',
    fontStyle: 'italic',
    marginBottom: 5,
  },
  partOfSpeech: {
    fontSize: 14,
    color: '#999',
    fontStyle: 'italic',
  },
  actionButtons: {
    flexDirection: 'row',
  },
  actionButton: {
    padding: 10,
    marginLeft: 10,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 20,
  },
  translationSection: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 15,
  },
  bengaliText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#64FFDA',
    flex: 1,
  },
  speakBengali: {
    padding: 8,
    backgroundColor: 'rgba(100, 255, 218, 0.2)',
    borderRadius: 15,
  },
  definition: {
    fontSize: 16,
    color: '#ccc',
    lineHeight: 24,
    marginBottom: 15,
  },
  examplesSection: {
    marginTop: 10,
  },
  examplesTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#64FFDA',
    marginBottom: 10,
  },
  example: {
    fontSize: 14,
    color: '#999',
    lineHeight: 20,
    marginBottom: 5,
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 18,
    color: '#666',
    marginTop: 20,
    marginBottom: 10,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#555',
    textAlign: 'center',
    paddingHorizontal: 40,
  },
  favoriteItem: {
    marginBottom: 12,
  },
  favoriteCard: {
    borderRadius: 15,
    padding: 15,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 107, 107, 0.2)',
  },
  favoriteContent: {
    flex: 1,
  },
  favoriteWord: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 5,
  },
  favoriteBengali: {
    fontSize: 16,
    color: '#FF6B6B',
  },
  historyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  clearHistoryButton: {
    paddingHorizontal: 15,
    paddingVertical: 8,
    backgroundColor: 'rgba(255, 107, 107, 0.2)',
    borderRadius: 15,
  },
  clearHistoryText: {
    color: '#FF6B6B',
    fontSize: 14,
    fontWeight: '600',
  },
  historyItem: {
    marginBottom: 10,
  },
  historyCard: {
    borderRadius: 12,
    padding: 15,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(100, 255, 218, 0.1)',
  },
  historyWord: {
    fontSize: 16,
    color: '#fff',
    flex: 1,
    marginLeft: 10,
  },
  historyTime: {
    fontSize: 12,
    color: '#666',
  },
  bottomNav: {
    flexDirection: 'row',
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    borderTopWidth: 1,
    borderTopColor: 'rgba(100, 255, 218, 0.2)',
    paddingVertical: 10,
    paddingHorizontal: 20,
  },
  navButton: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 10,
  },
  activeNavButton: {
    backgroundColor: 'rgba(100, 255, 218, 0.1)',
    borderRadius: 12,
  },
  navText: {
    fontSize: 12,
    color: '#666',
    marginTop: 4,
    fontWeight: '600',
  },
  activeNavText: {
    color: '#64FFDA',
  },
});